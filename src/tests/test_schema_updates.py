from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from src.app.model_registry import import_all_models
from src.app.schema_updates import REVISIONS, apply_schema_updates


def _engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _people_columns(engine):
    with engine.connect() as connection:
        return [row[1] for row in connection.execute(text("PRAGMA table_info(people)"))]


def _versions(engine):
    with engine.connect() as connection:
        return connection.execute(text("SELECT version FROM schema_migrations ORDER BY version")).scalars().all()


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
    assert _versions(engine) == list(REVISIONS)

    apply_schema_updates(engine)
    assert _versions(engine) == list(REVISIONS)


def test_events_revision_applies_on_top_of_revision_001():
    import_all_models()
    engine = _engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE schema_migrations (version VARCHAR PRIMARY KEY, applied_at TIMESTAMP)"))
        connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('001_people_groups_expansion')"))

    apply_schema_updates(engine)
    tables = set(inspect(engine).get_table_names())
    assert {"event_types", "event_series", "event_occurrences", "service_plan_items", "dashboard_layouts"} <= tables
    assert _versions(engine) == list(REVISIONS)
