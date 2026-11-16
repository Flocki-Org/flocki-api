from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from src.app.database import Base
from src.app.groups.models.database.models import Group  # noqa: F401
from src.app.media.models.database.models import MediaItem  # noqa: F401
from src.app.people.models.database.models import Address, Person  # noqa: F401
from src.app.worship.models.database.models import Song  # noqa: F401


def _naive_utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class EventType(Base):
    __tablename__ = "event_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    colour = Column(String)
    has_order_of_service = Column(Boolean, nullable=False, default=False)
    tracks_attendance = Column(Boolean, nullable=False, default=False)
    # "church" uses the church address by default; "address" asks for a full address record.
    default_location = Column(String, nullable=False, default="address")
    display_order = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ux_event_types_name", "name", unique=True),)


class EventSeries(Base):
    """The definition of an event. A once-off event is a series without a frequency."""

    __tablename__ = "event_series"
    id = Column(Integer, primary_key=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    image_id = Column(Integer, ForeignKey("media_items.id"))
    use_church_address = Column(Boolean, nullable=False, default=False)
    address_id = Column(Integer, ForeignKey("addresses.id"))
    venue = Column(String)
    online_url = Column(String)
    # Church-local wall-clock times, so 09:00 stays 09:00 across daylight-saving changes.
    start_date = Column(Date, nullable=False)
    start_time = Column(Time)
    end_time = Column(Time)
    all_day = Column(Boolean, nullable=False, default=False)
    frequency = Column(String)
    interval = Column(Integer, nullable=False, default=1)
    by_weekday = Column(String)
    by_set_pos = Column(String)
    until = Column(Date)
    status = Column(String, nullable=False, default="active")
    archived_at = Column(DateTime)
    created_by_user_id = Column(Integer)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    event_type = relationship("EventType")
    group = relationship("Group")
    image = relationship("MediaItem", foreign_keys=[image_id])
    address = relationship("Address", foreign_keys=[address_id])
    occurrences = relationship("EventOccurrence", back_populates="series", cascade="all, delete-orphan")
    template_items = relationship(
        "ServicePlanItem",
        primaryjoin="and_(EventSeries.id == ServicePlanItem.series_id, ServicePlanItem.occurrence_id.is_(None))",
        order_by="ServicePlanItem.position",
        viewonly=True,
    )
    __table_args__ = (
        Index("ix_event_series_type", "event_type_id"),
        Index("ix_event_series_group", "group_id"),
        Index("ix_event_series_status", "status"),
        Index("ix_event_series_dates", "start_date", "until"),
    )


class EventOccurrence(Base):
    """A saved date of a series. Only created once a date has something of its own."""

    __tablename__ = "event_occurrences"
    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey("event_series.id"), nullable=False)
    original_date = Column(Date, nullable=False)
    title = Column(String)
    description = Column(Text)
    image_id = Column(Integer, ForeignKey("media_items.id"))
    moved_to_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    location_override = Column(Boolean, nullable=False, default=False)
    use_church_address = Column(Boolean)
    address_id = Column(Integer, ForeignKey("addresses.id"))
    venue = Column(String)
    online_url = Column(String)
    status = Column(String, nullable=False, default="scheduled")
    cancel_reason = Column(Text)
    plan_status = Column(String, nullable=False, default="draft")
    plan_initialised = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    series = relationship("EventSeries", back_populates="occurrences")
    image = relationship("MediaItem", foreign_keys=[image_id])
    address = relationship("Address", foreign_keys=[address_id])
    plan_items = relationship(
        "ServicePlanItem",
        back_populates="occurrence",
        order_by="ServicePlanItem.position",
        cascade="all, delete-orphan",
    )
    __table_args__ = (
        Index("ux_event_occurrence_series_date", "series_id", "original_date", unique=True),
        Index("ix_event_occurrence_moved", "moved_to_date"),
        Index("ix_event_occurrence_status", "status"),
    )


class ServicePlanItem(Base):
    """An order-of-service line. Belongs to a series template or to one occurrence, never both."""

    __tablename__ = "service_plan_items"
    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey("event_series.id"))
    occurrence_id = Column(Integer, ForeignKey("event_occurrences.id"))
    position = Column(Integer, nullable=False, default=0)
    item_type = Column(String, nullable=False)
    title = Column(String)
    song_id = Column(Integer, ForeignKey("songs.id"))
    song_key = Column(String)
    scripture_reference = Column(String)
    person_id = Column(Integer, ForeignKey("people.id"))
    person_name = Column(String)
    duration_minutes = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=_naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    occurrence = relationship("EventOccurrence", back_populates="plan_items")
    song = relationship("Song")
    person = relationship("Person")
    __table_args__ = (
        Index("ix_service_plan_items_series", "series_id"),
        Index("ix_service_plan_items_occurrence", "occurrence_id"),
        Index("ix_service_plan_items_song", "song_id"),
    )
