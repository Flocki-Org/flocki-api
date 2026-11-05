from __future__ import annotations

import logging
import os
import re
import socket
import time
from typing import Optional
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

logger = logging.getLogger(__name__)

# Bare Render private hostname, e.g. dpg-cf2601g2i3mnjcmtd030-a
_RENDER_INTERNAL_HOST = re.compile(r"^dpg-[a-z0-9]+-a$", re.IGNORECASE)


def _normalize_sqlalchemy_url(url: str) -> str:
    """SQLAlchemy 2.1 maps postgresql:// to psycopg3; this app uses psycopg2."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


def _host_resolves(host: str, port: int = 5432) -> bool:
    try:
        socket.getaddrinfo(host, port)
        return True
    except socket.gaierror:
        return False


def resolve_database_host(
    host: str,
    render_region: Optional[str] = None,
) -> str:
    """
    Keep a working host as-is. If it is a bare Render internal id that does not
    resolve (typical region mismatch), rewrite to the public hostname using
    render_region.
    """
    if not _RENDER_INTERNAL_HOST.fullmatch(host):
        return host

    if _host_resolves(host):
        return host

    region = (render_region or "").strip().lower()
    if not region:
        # Bare internal hosts fail DNS when the web service is in another region
        # (or private DNS is unavailable). Oregon is Render's historical default
        # and unblocks that case via the public hostname; override with
        # FLOCKI_API_DB_RENDER_REGION when the DB lives elsewhere.
        region = "oregon"
        logger.warning(
            "Render internal DB host %r did not resolve and "
            "FLOCKI_API_DB_RENDER_REGION is unset; defaulting to %r. "
            "Set FLOCKI_API_DB_RENDER_REGION or FLOCKI_API_DB_HOST to the "
            "External hostname from the Render Connect menu if this is wrong.",
            host,
            region,
        )

    external = f"{host}.{region}-postgres.render.com"
    logger.warning(
        "Render internal DB host %r did not resolve; using external host %r",
        host,
        external,
    )
    return external


def _ensure_sslmode(url: str, sslmode: Optional[str]) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    host = parsed.hostname or ""

    mode = sslmode
    if mode is None and ("render.com" in host or _RENDER_INTERNAL_HOST.fullmatch(host or "")):
        mode = "require"

    if mode:
        query["sslmode"] = mode

    return urlunparse(parsed._replace(query=urlencode(query)))


def build_database_url(
    *,
    database_url: Optional[str] = None,
    user_name: str = "postgres",
    password: str = "password",
    host: str = "localhost",
    port: int = 5432,
    db_name: str = "flocki_api",
    render_region: Optional[str] = None,
    sslmode: Optional[str] = None,
) -> str:
    if database_url:
        url = _normalize_sqlalchemy_url(database_url.strip())
        parsed = urlparse(url)
        if parsed.hostname and _RENDER_INTERNAL_HOST.fullmatch(parsed.hostname):
            new_host = resolve_database_host(parsed.hostname, render_region)
            if new_host != parsed.hostname:
                userinfo = ""
                if parsed.username is not None:
                    userinfo = quote_plus(parsed.username)
                    if parsed.password is not None:
                        userinfo += f":{quote_plus(parsed.password)}"
                    userinfo += "@"
                netloc = f"{userinfo}{new_host}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                url = urlunparse(parsed._replace(netloc=netloc))
        return _ensure_sslmode(url, sslmode)

    resolved_host = resolve_database_host(host, render_region)
    user = quote_plus(user_name)
    pwd = quote_plus(password)
    url = (
        f"postgresql+psycopg2://{user}:{pwd}"
        f"@{resolved_host}:{port}/{db_name}"
    )
    return _ensure_sslmode(url, sslmode)


SQLALCHEMY_DATABASE_URL = build_database_url(
    database_url=settings.flocki_api_database_url,
    user_name=settings.flocki_api_db_user_name,
    password=settings.flocki_api_db_password,
    host=settings.flocki_api_db_host,
    port=settings.flocki_api_db_port,
    db_name=settings.flocki_api_db_name,
    render_region=settings.flocki_api_db_render_region,
    sslmode=settings.flocki_api_db_sslmode,
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 8, delay_seconds: float = 2.0) -> None:
    """Create tables, retrying briefly so Render deploys survive slow DNS/DB ready."""
    last_error: Optional[BaseException] = None
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            logger.info("Database schema ready (attempt %s/%s)", attempt, retries)
            return
        except Exception as exc:  # noqa: BLE001 - surface final error after retries
            last_error = exc
            logger.warning(
                "Database init attempt %s/%s failed: %s",
                attempt,
                retries,
                exc,
            )
            if attempt < retries:
                time.sleep(delay_seconds)

    assert last_error is not None
    raise last_error


def running_on_render() -> bool:
    return os.environ.get("RENDER", "").lower() in {"true", "1", "yes"}
