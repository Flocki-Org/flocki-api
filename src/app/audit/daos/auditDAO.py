from datetime import datetime

from fastapi import Depends

from src.app.audit.models.database.models import AuditLog
from src.app.database import SessionLocal, get_db
from src.app.imports.models.database.models import ExternalReference, ImportErrorRecord
from src.app.people.personFields import SENSITIVE_PERSON_FIELDS


def _jsonable(value):
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def safe_summary(data):
    if data is None:
        return None
    cleaned = {}
    for key, value in data.items():
        if key in SENSITIVE_PERSON_FIELDS or key in {"notes", "raw", "raw_payload", "password"}:
            cleaned[key] = "updated" if value not in (None, "", [], {}) else None
        else:
            cleaned[key] = _jsonable(value)
    return cleaned


class AuditDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def record(self, entity_type, entity_id, action, summary=None, actor_user_id=None):
        self.db.add(AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user_id=actor_user_id,
            summary=safe_summary(summary),
        ))

    def for_entity(self, entity_type, entity_id):
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )


class ImportDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_reference(self, source, entity_type, external_id):
        return (
            self.db.query(ExternalReference)
            .filter(
                ExternalReference.source == source,
                ExternalReference.entity_type == entity_type,
                ExternalReference.external_id == str(external_id),
            )
            .first()
        )

    def save_reference(self, source, entity_type, entity_id, external_id, raw_payload):
        existing = self.get_reference(source, entity_type, external_id)
        if existing is None:
            existing = ExternalReference(
                source=source,
                entity_type=entity_type,
                entity_id=entity_id,
                external_id=str(external_id),
            )
            self.db.add(existing)
        existing.entity_id = entity_id
        existing.imported_at = datetime.now()
        existing.raw_payload = raw_payload
        self.db.flush()
        return existing

    def add_error(self, source, entity_type, external_id, message, payload):
        self.db.add(ImportErrorRecord(
            source=source,
            entity_type=entity_type,
            external_id=None if external_id is None else str(external_id),
            message=message[:2000],
            payload=payload,
        ))
        self.db.commit()

    def list_errors(self, source=None):
        query = self.db.query(ImportErrorRecord).order_by(ImportErrorRecord.created_at.desc())
        if source:
            query = query.filter(ImportErrorRecord.source == source)
        return query.limit(200).all()
