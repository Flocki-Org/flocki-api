from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from src.app.database import Base
from src.app.media.models.database.models import MediaItem  # noqa: F401
from src.app.people.models.database.models import Address, Person  # noqa: F401


def _naive_utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class GroupCategory(Base):
    __tablename__ = "group_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    colour = Column(String)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ux_group_categories_name", "name", unique=True),)


class GroupRole(Base):
    __tablename__ = "group_roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    active = Column(Boolean, nullable=False, default=True)
    is_leader = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ux_group_roles_name", "name", unique=True),)


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("group_categories.id"))
    status = Column(String, nullable=False, default="active")
    meeting_location = Column(String)
    meeting_address_id = Column(Integer, ForeignKey("addresses.id"))
    meeting_day = Column(String)
    meeting_start_time = Column(Time)
    meeting_end_time = Column(Time)
    meeting_frequency = Column(String)
    meeting_notes = Column(Text)
    contact_email = Column(String)
    contact_phone = Column(String)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    archived_at = Column(DateTime)
    category = relationship("GroupCategory")
    meeting_address = relationship("Address")
    memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")
    images = relationship("GroupImage", back_populates="group", cascade="all, delete-orphan")
    __table_args__ = (
        Index("ix_groups_name", "name"),
        Index("ix_groups_status", "status"),
        Index("ix_groups_category", "category_id"),
    )


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("group_roles.id"))
    status = Column(String, nullable=False, default="active")
    date_joined = Column(Date)
    date_left = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    group = relationship("Group", back_populates="memberships")
    person = relationship("Person")
    role = relationship("GroupRole")
    __table_args__ = (
        Index("ux_group_membership_person", "group_id", "person_id", unique=True),
        Index("ix_group_membership_person", "person_id"),
        Index("ix_group_membership_status", "status"),
        Index("ix_group_membership_role", "role_id"),
    )


class GroupImage(Base):
    __tablename__ = "group_images"
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("media_items.id"), nullable=False)
    group = relationship("Group", back_populates="images")
    image = relationship("MediaItem")
