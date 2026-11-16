from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from src.app.model_registry import import_all_models
from src.app.schema_updates import REVISION, apply_schema_updates


def _engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _people_columns(engine):
    with engine.connect() as connection:
        return [row[1] for row in connection.execute(text("PRAGMA table_info(people)"))]


def test_column_sync_preserves_existing_rows_and_transaction_rolls_back():
    import_all_models()
    engine = _engine()
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE people (id INTEGER PRIMARY KEY, first_name VARCHAR, last_name VARCHAR)"
        ))
        connection.execute(text(
            "INSERT INTO people (id, first_name, last_name) VALUES (1, 'Ada', 'Lovelace')"
        ))

    try:
        with engine.begin() as connection:
            connection.execute(text("UPDATE people SET first_name = 'Changed' WHERE id = 1"))
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass

    with engine.connect() as connection:
        assert connection.execute(text("SELECT first_name FROM people WHERE id = 1")).scalar() == "Ada"

    apply_schema_updates(engine)
    columns = _people_columns(engine)
    assert "preferred_name" in columns
    assert "lifecycle_status" in columns
    with engine.connect() as connection:
        assert connection.execute(text("SELECT first_name, last_name FROM people WHERE id = 1")).one() == ("Ada", "Lovelace")
        assert connection.execute(text("SELECT version FROM schema_migrations")).scalar() == REVISION

    apply_schema_updates(engine)
    with engine.connect() as connection:
        versions = connection.execute(text("SELECT version FROM schema_migrations")).scalars().all()
    assert versions == [REVISION]
