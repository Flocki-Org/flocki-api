import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.app.people.models.people import ViewAddress

PLAN_ITEM_TYPES = ("song", "reading", "sermon", "prayer", "communion", "offering", "notices", "baptism", "custom")
PlanItemType = Literal["song", "reading", "sermon", "prayer", "communion", "offering", "notices", "baptism", "custom"]
EditScope = Literal["this", "following", "all"]


class EventTypeInput(BaseModel):
    name: str
    description: Optional[str] = None
    colour: Optional[str] = None
    has_order_of_service: bool = False
    tracks_attendance: bool = False
    default_location: Literal["church", "address"] = "address"
    display_order: int = 0
    active: bool = True

    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "Youth service", "colour": "#7C3AED", "has_order_of_service": True,
        "tracks_attendance": True, "default_location": "church",
    }})


class EventTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    colour: Optional[str] = None
    has_order_of_service: Optional[bool] = None
    tracks_attendance: Optional[bool] = None
    default_location: Optional[Literal["church", "address"]] = None
    display_order: Optional[int] = None
    active: Optional[bool] = None


class EventTypeView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    colour: Optional[str] = None
    has_order_of_service: bool = False
    tracks_attendance: bool = False
    default_location: str = "address"
    display_order: int = 0
    active: bool = True


class RecurrenceInput(BaseModel):
    frequency: Literal["weekly", "monthly", "yearly"]
    interval: int = Field(1, ge=1, le=52)
    weekdays: List[Literal["MO", "TU", "WE", "TH", "FR", "SA", "SU"]] = Field(default_factory=list)
    positions: List[int] = Field(default_factory=list, description="Week of the month: 1 to 5, or -1 for the last")
    until: Optional[datetime.date] = None


class RecurrenceView(RecurrenceInput):
    label: str


class LocationInput(BaseModel):
    use_church_address: bool = False
    address_id: Optional[int] = None
    venue: Optional[str] = None
    online_url: Optional[str] = None


class LocationView(BaseModel):
    use_church_address: bool = False
    address: Optional[ViewAddress] = None
    venue: Optional[str] = None
    online_url: Optional[str] = None


class CreateEvent(BaseModel):
    event_type_id: int
    title: str
    description: Optional[str] = None
    group_id: Optional[int] = None
    start_date: datetime.date
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    all_day: bool = False
    location: Optional[LocationInput] = None
    recurrence: Optional[RecurrenceInput] = None

    @model_validator(mode="after")
    def check_times(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("End time must be after the start time")
        return self

    model_config = ConfigDict(json_schema_extra={"example": {
        "event_type_id": 1,
        "title": "Sunday Morning Service",
        "start_date": "2026-11-22",
        "start_time": "09:00:00",
        "end_time": "10:30:00",
        "location": {"use_church_address": True},
        "recurrence": {"frequency": "weekly", "weekdays": ["SU"]},
    }})


class UpdateEventSeries(BaseModel):
    event_type_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[int] = None
    start_date: Optional[datetime.date] = None
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    all_day: Optional[bool] = None
    location: Optional[LocationInput] = None
    recurrence: Optional[RecurrenceInput] = None


class UpdateOccurrence(BaseModel):
    """Edit one date of a series. `scope` decides how far the change reaches."""

    scope: EditScope = "this"
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime.date] = Field(None, description="Move this occurrence to another date (scope 'this' only)")
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    all_day: Optional[bool] = None
    location: Optional[LocationInput] = None
    event_type_id: Optional[int] = None
    group_id: Optional[int] = None
    recurrence: Optional[RecurrenceInput] = None

    model_config = ConfigDict(json_schema_extra={"example": {"scope": "this", "title": "Easter Sunday"}})


class CancelOccurrence(BaseModel):
    reason: Optional[str] = None


class CancelRange(BaseModel):
    start: datetime.date
    end: datetime.date
    reason: Optional[str] = None

    @model_validator(mode="after")
    def check_range(self):
        if self.end < self.start:
            raise ValueError("End must be on or after start")
        return self


class DuplicateEvent(BaseModel):
    date: datetime.date
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    title: Optional[str] = None


class SeriesView(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    event_type: EventTypeView
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    image_id: Optional[int] = None
    location: LocationView
    start_date: datetime.date
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    all_day: bool = False
    recurrence: Optional[RecurrenceView] = None
    schedule_label: str
    next_date: Optional[datetime.date] = None
    status: str


class OccurrenceView(BaseModel):
    key: str = Field(description="Stable reference: '<series_id>:<original_date>'")
    id: Optional[int] = Field(None, description="Set once the occurrence has been saved")
    series_id: int
    original_date: datetime.date
    date: datetime.date
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    all_day: bool = False
    title: str
    description: Optional[str] = None
    event_type: EventTypeView
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    image_id: Optional[int] = None
    location: LocationView
    is_recurring: bool
    schedule_label: str
    status: str
    cancel_reason: Optional[str] = None
    overridden_fields: List[str] = Field(default_factory=list)
    plan_state: Optional[Literal["not_started", "draft", "final"]] = None
    plan_item_count: int = 0


class PlanItemInput(BaseModel):
    item_type: PlanItemType
    title: Optional[str] = None
    song_id: Optional[int] = None
    song_key: Optional[str] = None
    scripture_reference: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0, le=600)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def song_needs_song(self):
        if self.item_type == "song" and not self.song_id and not self.title:
            raise ValueError("A song item needs a song from the library or a title")
        return self


class PlanItemView(PlanItemInput):
    id: int
    position: int
    song_name: Optional[str] = None
    song_ccli_number: Optional[str] = None
    song_default_key: Optional[str] = None
    person_display_name: Optional[str] = None
    planned_start: Optional[datetime.time] = None


class TemplateInput(BaseModel):
    items: List[PlanItemInput] = Field(default_factory=list)


class PlanInput(BaseModel):
    status: Literal["draft", "final"] = "draft"
    items: List[PlanItemInput] = Field(default_factory=list)

    model_config = ConfigDict(json_schema_extra={"example": {
        "status": "draft",
        "items": [
            {"item_type": "song", "song_id": 1, "song_key": "G", "duration_minutes": 4},
            {"item_type": "reading", "scripture_reference": "John 1:1-14", "person_name": "Guest reader", "duration_minutes": 3},
            {"item_type": "sermon", "title": "The Word became flesh", "scripture_reference": "John 1:14", "person_id": 1, "duration_minutes": 30},
        ],
    }})


class PlanView(BaseModel):
    occurrence: OccurrenceView
    initialised: bool
    status: Literal["draft", "final"]
    total_minutes: int
    items: List[PlanItemView]


class SongUsageView(BaseModel):
    song_id: int
    name: Optional[str] = None
    code: Optional[str] = None
    ccli_number: Optional[str] = None
    times_used: int
    last_used: Optional[datetime.date] = None


class SongHistoryEntry(BaseModel):
    date: datetime.date
    series_id: int
    title: str
    song_key: Optional[str] = None
    cancelled: bool = False


class SongUsageDetail(BaseModel):
    song_id: int
    times_used_last_12_months: int
    last_used: Optional[datetime.date] = None
    next_scheduled: Optional[datetime.date] = None
    history: List[SongHistoryEntry]
