from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from src.app.database import Base
from src.app.database_types import portable_json


def _naive_utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class ExternalReference(Base):
    __tablename__ = "external_references"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    external_id = Column(String, nullable=False)
    imported_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    raw_payload = Column(portable_json())
    __table_args__ = (
        Index("ux_external_reference", "source", "entity_type", "external_id", unique=True),
        Index("ix_external_reference_entity", "entity_type", "entity_id"),
    )


class ImportErrorRecord(Base):
    __tablename__ = "import_errors"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    entity_type = Column(String)
    external_id = Column(String)
    message = Column(Text, nullable=False)
    payload = Column(portable_json())
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ix_import_errors_source", "source", "entity_type"),)
