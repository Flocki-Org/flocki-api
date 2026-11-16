from fastapi import Depends
from sqlalchemy.orm import selectinload

from src.app.customfields.models.database import models
from src.app.database import SessionLocal, get_db


class CustomFieldDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def list_definitions(self, entity_type=None, include_inactive=False):
        query = (
            self.db.query(models.CustomFieldDefinition)
            .options(selectinload(models.CustomFieldDefinition.options))
            .order_by(models.CustomFieldDefinition.display_order.asc(), models.CustomFieldDefinition.name.asc())
        )
        if entity_type:
            query = query.filter(models.CustomFieldDefinition.entity_type == entity_type)
        if not include_inactive:
            query = query.filter(models.CustomFieldDefinition.active.is_(True))
        return query.all()

    def get(self, field_id):
        return (
            self.db.query(models.CustomFieldDefinition)
            .options(selectinload(models.CustomFieldDefinition.options))
            .filter(models.CustomFieldDefinition.id == field_id)
            .first()
        )

    def get_by_name(self, entity_type, name):
        return (
            self.db.query(models.CustomFieldDefinition)
            .filter(
                models.CustomFieldDefinition.entity_type == entity_type,
                models.CustomFieldDefinition.name == name,
            )
            .first()
        )

    def add(self, field):
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return self.get(field.id)

    def save(self, field):
        self.db.commit()
        return self.get(field.id)

    def delete(self, field):
        self.db.delete(field)
        self.db.commit()

    def has_values(self, field_id):
        return (
            self.db.query(models.CustomFieldValue)
            .filter(models.CustomFieldValue.field_id == field_id)
            .first()
            is not None
        )

    def values_for_entity(self, entity_type, entity_id):
        return (
            self.db.query(models.CustomFieldValue)
            .options(selectinload(models.CustomFieldValue.field).selectinload(models.CustomFieldDefinition.options))
            .filter(
                models.CustomFieldValue.entity_type == entity_type,
                models.CustomFieldValue.entity_id == entity_id,
            )
            .all()
        )

    def get_value(self, field_id, entity_type, entity_id):
        return (
            self.db.query(models.CustomFieldValue)
            .filter(
                models.CustomFieldValue.field_id == field_id,
                models.CustomFieldValue.entity_type == entity_type,
                models.CustomFieldValue.entity_id == entity_id,
            )
            .first()
        )

    def add_value(self, value):
        self.db.add(value)
        return value

    def delete_value(self, value):
        self.db.delete(value)
