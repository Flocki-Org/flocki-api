from urllib.parse import parse_qs, urlparse

import pytest

from src.app.database import (
    build_database_url,
    resolve_database_host,
    _normalize_sqlalchemy_url,
)


def test_normalize_postgres_schemes():
    assert _normalize_sqlalchemy_url("postgres://u:p@h/db").startswith(
        "postgresql+psycopg2://"
    )
    assert _normalize_sqlalchemy_url("postgresql://u:p@h/db").startswith(
        "postgresql+psycopg2://"
    )
    assert _normalize_sqlalchemy_url("postgresql+psycopg2://u:p@h/db").startswith(
        "postgresql+psycopg2://"
    )


def test_build_url_from_components_encodes_password():
    url = build_database_url(
        user_name="user",
        password="p@ss/word",
        host="localhost",
        port=5432,
        db_name="flocki_api",
    )
    assert url.startswith("postgresql+psycopg2://user:p%40ss%2Fword@localhost:5432/flocki_api")


def test_build_url_prefers_database_url():
    url = build_database_url(
        database_url="postgresql://u:p@db.example:5432/mydb",
        host="ignored",
    )
    assert url.startswith("postgresql+psycopg2://u:p@db.example:5432/mydb")


def test_render_external_host_gets_sslmode_require():
    url = build_database_url(
        user_name="u",
        password="p",
        host="dpg-abc123-a.oregon-postgres.render.com",
        db_name="flocki",
    )
    query = parse_qs(urlparse(url).query)
    assert query["sslmode"] == ["require"]


def test_database_url_render_gets_sslmode_require():
    url = build_database_url(
        database_url="postgresql://u:p@dpg-abc123-a.oregon-postgres.render.com/flocki"
    )
    query = parse_qs(urlparse(url).query)
    assert query["sslmode"] == ["require"]


def test_explicit_sslmode_override():
    url = build_database_url(
        host="localhost",
        user_name="u",
        password="p",
        db_name="flocki",
        sslmode="disable",
    )
    query = parse_qs(urlparse(url).query)
    assert query["sslmode"] == ["disable"]


def test_resolve_non_render_host_unchanged():
    assert resolve_database_host("localhost") == "localhost"
    assert resolve_database_host("db.internal") == "db.internal"


def test_resolve_bare_render_host_expands_with_region(monkeypatch):
    monkeypatch.setattr(
        "src.app.database._host_resolves",
        lambda host, port=5432: False,
    )
    assert (
        resolve_database_host("dpg-cf2601g2i3mnjcmtd030-a", render_region="frankfurt")
        == "dpg-cf2601g2i3mnjcmtd030-a.frankfurt-postgres.render.com"
    )


def test_resolve_bare_render_host_defaults_oregon_when_unresolved(monkeypatch):
    monkeypatch.setattr(
        "src.app.database._host_resolves",
        lambda host, port=5432: False,
    )
    assert (
        resolve_database_host("dpg-cf2601g2i3mnjcmtd030-a")
        == "dpg-cf2601g2i3mnjcmtd030-a.oregon-postgres.render.com"
    )


def test_resolve_bare_render_host_kept_when_dns_works(monkeypatch):
    monkeypatch.setattr(
        "src.app.database._host_resolves",
        lambda host, port=5432: True,
    )
    assert resolve_database_host("dpg-cf2601g2i3mnjcmtd030-a") == "dpg-cf2601g2i3mnjcmtd030-a"


def test_database_url_rewrites_unresolved_internal_host(monkeypatch):
    monkeypatch.setattr(
        "src.app.database._host_resolves",
        lambda host, port=5432: False,
    )
    url = build_database_url(
        database_url="postgresql://u:p@dpg-cf2601g2i3mnjcmtd030-a:5432/flocki",
        render_region="ohio",
    )
    parsed = urlparse(url)
    assert parsed.hostname == "dpg-cf2601g2i3mnjcmtd030-a.ohio-postgres.render.com"
    assert parse_qs(parsed.query)["sslmode"] == ["require"]
