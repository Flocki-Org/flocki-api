from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB


def portable_json():
    """JSON on SQLite, JSONB on PostgreSQL."""
    return JSON().with_variant(JSONB(), "postgresql")
