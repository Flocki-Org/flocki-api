from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.app.database import Base
from src.app.database_types import portable_json


def _naive_utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class CustomFieldDefinition(Base):
    __tablename__ = "custom_field_definitions"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    field_type = Column(String, nullable=False)
    required = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    default_value = Column(Text)
    entity_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    options = relationship(
        "CustomFieldOption",
        back_populates="field",
        cascade="all, delete-orphan",
    )
    __table_args__ = (
        Index("ux_custom_field_entity_name", "entity_type", "name", unique=True),
        Index("ix_custom_field_entity_active", "entity_type", "active"),
    )


class CustomFieldOption(Base):
    __tablename__ = "custom_field_options"
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("custom_field_definitions.id"), nullable=False)
    value = Column(String, nullable=False)
    label = Column(String, nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    field = relationship("CustomFieldDefinition", back_populates="options")
    __table_args__ = (Index("ux_custom_field_option", "field_id", "value", unique=True),)


class CustomFieldValue(Base):
    __tablename__ = "custom_field_values"
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("custom_field_definitions.id"), nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    value_text = Column(Text)
    value_number = Column(Integer)
    value_decimal = Column(Numeric(14, 4))
    value_date = Column(Date)
    value_bool = Column(Boolean)
    value_json = Column(portable_json())
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    field = relationship("CustomFieldDefinition")
    __table_args__ = (
        Index("ux_custom_field_value_entity", "field_id", "entity_type", "entity_id", unique=True),
        Index("ix_custom_field_value_entity", "entity_type", "entity_id"),
    )
