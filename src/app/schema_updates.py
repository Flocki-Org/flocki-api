"""Versioned, idempotent schema updates for databases that already have data.

`Base.metadata.create_all` creates missing tables and is not enough on its own:
it does not add columns to tables that already exist. Revision 001 adds those
columns and indexes without dropping anything.

PostgreSQL DDL runs inside a transaction, so a failure rolls the revision back.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine

from src.app.database import Base, engine as default_engine
from src.app.model_registry import import_all_models

logger = logging.getLogger(__name__)

REVISION = "001_people_groups_expansion"
SQL_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


def apply_schema_updates(bound_engine: Engine | None = None) -> None:
    import_all_models()
    db_engine = bound_engine or default_engine
    Base.metadata.create_all(bind=db_engine)
    with db_engine.begin() as connection:
        _ensure_migrations_table(connection)
        applied = _applied_versions(connection)
        if REVISION not in applied and connection.dialect.name == "postgresql":
            _apply_sql_file(connection, SQL_DIR / f"{REVISION}.sql")
        _sync_missing_columns(connection)
        _sync_missing_indexes(connection)
        if REVISION not in applied:
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": REVISION},
            )
            logger.info("Applied schema revision %s", REVISION)


def _ensure_migrations_table(connection: Connection) -> None:
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _applied_versions(connection: Connection) -> set[str]:
    rows = connection.execute(text("SELECT version FROM schema_migrations"))
    return {row[0] for row in rows}


def _apply_sql_file(connection: Connection, path: Path) -> None:
    if not path.exists():
        logger.info("No SQL file at %s; column sync still runs", path)
        return
    script = path.read_text()
    for statement in _statements(script):
        connection.execute(text(statement))


def _statements(script: str) -> list[str]:
    statements = []
    for chunk in script.split(";"):
        lines = []
        for line in chunk.splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            lines.append(line)
        statement = "\n".join(lines).strip()
        if statement:
            statements.append(statement)
    return statements


def _sync_missing_columns(connection: Connection) -> None:
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue
            column_type = column.type.compile(dialect=connection.dialect)
            # Always nullable. A NOT NULL column without a server default cannot
            # be added to a populated table.
            connection.execute(
                text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type} NULL')
            )
            existing_columns.add(column.name)
            logger.info("Added column %s.%s", table.name, column.name)


def _sync_missing_indexes(connection: Connection) -> None:
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_indexes = {index["name"] for index in inspector.get_indexes(table.name)}
        for index in table.indexes:
            if not index.name or index.name in existing_indexes:
                continue
            index.create(bind=connection)
            logger.info("Added index %s on %s", index.name, table.name)
