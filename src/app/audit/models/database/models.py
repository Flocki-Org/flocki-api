from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Index, Integer, String

from src.app.database import Base
from src.app.database_types import portable_json


def _naive_utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    actor_user_id = Column(Integer)
    summary = Column(portable_json())
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ix_audit_logs_entity", "entity_type", "entity_id", "created_at"),)
