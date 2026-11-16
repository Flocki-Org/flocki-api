import datetime

from fastapi import Depends

from src.app.events import recurrence
from src.app.events.daos.eventDAO import EventDAO
from src.app.events.models.database import models
from src.app.events.models.events import (
    CancelRange,
    CreateEvent,
    DuplicateEvent,
    EventTypeInput,
    EventTypeUpdate,
    EventTypeView,
    LocationInput,
    LocationView,
    OccurrenceView,
    PlanInput,
    PlanItemInput,
    PlanItemView,
    PlanView,
    RecurrenceInput,
    RecurrenceView,
    SeriesView,
    TemplateInput,
    UpdateEventSeries,
    UpdateOccurrence,
)
from src.app.groups.models.database.models import Group
from src.app.people.models.database.models import Address, Person
from src.app.people.models.people import ViewAddress

MAX_WINDOW_DAYS = 400


class NoEventTypeException(Exception):
    pass


class EventTypeInUseException(Exception):
    pass


class NoSeriesException(Exception):
    pass


class NoOccurrenceException(Exception):
    pass


class InvalidEventException(ValueError):
    pass


class NoOrderOfServiceException(Exception):
    pass


def occurrence_key(series_id, original_date):
    return f"{series_id}:{original_date.isoformat()}"


def parse_key(key):
    try:
        series_id, day = key.split(":", 1)
        return int(series_id), datetime.date.fromisoformat(day)
    except (ValueError, AttributeError):
        raise NoOccurrenceException("Occurrence key must look like '<series_id>:<YYYY-MM-DD>'")


def address_view(address):
    if address is None:
        return None
    return ViewAddress(
        id=address.id,
        type=address.type,
        building=address.building,
        unit=address.unit,
        street_number=address.street_number,
        street=address.street,
        suburb=address.suburb,
        city=address.city,
        province=address.province,
        country=address.country,
        postal_code=address.postal_code,
        latitude=address.latitude,
        longitude=address.longitude,
    )


def type_view(event_type):
    return EventTypeView(
        id=event_type.id,
        name=event_type.name,
        description=event_type.description,
        colour=event_type.colour,
        has_order_of_service=bool(event_type.has_order_of_service),
        tracks_attendance=bool(event_type.tracks_attendance),
        default_location=event_type.default_location or "address",
        display_order=event_type.display_order or 0,
        active=bool(event_type.active),
    )


def _person_name(person):
    if person is None:
        return None
    first = person.preferred_name or person.first_name or ""
    return " ".join(part for part in (first, person.last_name) if part) or None


class EventService:
    def __init__(self, dao: EventDAO = Depends(EventDAO)):
        self.dao = dao
        self._church_address_loaded = False
        self._church_address = None

    # Event types

    def list_types(self, include_inactive=False):
        return [type_view(row) for row in self.dao.list_types(include_inactive)]

    def create_type(self, payload: EventTypeInput):
        if self.dao.get_type_by_name(payload.name):
            raise EventTypeInUseException("An event type with that name already exists")
        return type_view(self.dao.add_type(models.EventType(**payload.model_dump())))

    def update_type(self, type_id, payload: EventTypeUpdate):
        event_type = self._require_type(type_id, allow_inactive=True)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            existing = self.dao.get_type_by_name(data["name"])
            if existing and existing.id != event_type.id:
                raise EventTypeInUseException("An event type with that name already exists")
        for key, value in data.items():
            setattr(event_type, key, value)
        return type_view(self.dao.save_type(event_type))

    def delete_type(self, type_id):
        """Deactivate a type that events still use; delete it otherwise."""
        event_type = self._require_type(type_id, allow_inactive=True)
        if self.dao.type_in_use(type_id):
            event_type.active = False
            return type_view(self.dao.save_type(event_type))
        self.dao.delete_type(event_type)
        return None

    # Series

    def create(self, payload: CreateEvent, actor_user_id=None):
        event_type = self._require_type(payload.event_type_id)
        self._require_group(payload.group_id)
        schedule = self._schedule(payload.start_date, payload.recurrence)
        location = payload.location or LocationInput(use_church_address=event_type.default_location == "church")
        self._require_address(location.address_id)
        series = models.EventSeries(
            event_type_id=event_type.id,
            group_id=payload.group_id,
            title=payload.title.strip(),
            description=payload.description,
            start_date=payload.start_date,
            start_time=None if payload.all_day else payload.start_time,
            end_time=None if payload.all_day else payload.end_time,
            all_day=payload.all_day,
            created_by_user_id=actor_user_id,
        )
        self._apply_location(series, location)
        self._apply_schedule(series, schedule)
        return self.series_view(self.dao.add_series(series))

    def get_series(self, series_id):
        return self.series_view(self._require_series(series_id))

    def list_series(self, type_id=None, group_id=None, include_archived=False):
        return [self.series_view(row) for row in self.dao.list_series(type_id, group_id, include_archived)]

    def update_series(self, series_id, payload: UpdateEventSeries):
        """Change every occurrence of a series."""
        series = self._require_series(series_id)
        changes = payload.model_dump(exclude_unset=True)
        self._apply_series_changes(series, changes)
        self._clear_overrides(self.dao.occurrences_for_series(series.id), changes)
        self._drop_unscheduled(series)
        self.dao.save()
        return self.series_view(self.dao.get_series(series.id))

    def archive_series(self, series_id):
        series = self._require_series(series_id)
        series.status = "archived"
        series.archived_at = datetime.datetime.now()
        return self.series_view(self.dao.save_series(series))

    def restore_series(self, series_id):
        series = self._require_series(series_id)
        series.status = "active"
        series.archived_at = None
        return self.series_view(self.dao.save_series(series))

    def set_series_image(self, series_id, image_id):
        series = self._require_series(series_id)
        series.image_id = image_id
        return self.series_view(self.dao.save_series(series))

    def duplicate_series(self, series_id, payload: DuplicateEvent, actor_user_id=None):
        """Copy a whole series, schedule included, so it starts on another date."""
        source = self._require_series(series_id)
        shift = payload.date - source.start_date
        copy = self._copy_series(source)
        copy.title = payload.title or source.title
        copy.start_date = payload.date
        copy.until = source.until + shift if source.until else None
        if payload.start_time is not None:
            copy.start_time = payload.start_time
        if payload.end_time is not None:
            copy.end_time = payload.end_time
        copy.created_by_user_id = actor_user_id
        self._validate_series(copy)
        created = self.dao.add_series(copy)
        self._copy_template(source.id, created.id)
        self.dao.save()
        return self.series_view(self.dao.get_series(created.id))

    # Occurrences

    def list_occurrences(self, start, end, type_ids=None, group_id=None, include_cancelled=True,
                         order_of_service_only=False):
        if end < start:
            raise InvalidEventException("End must be on or after start")
        if (end - start).days > MAX_WINDOW_DAYS:
            raise InvalidEventException(f"Ask for at most {MAX_WINDOW_DAYS} days at a time")
        series_rows = {
            row.id: row for row in self.dao.series_in_window(start, end, type_ids, group_id, order_of_service_only)
        }
        saved = {}
        for occurrence in self.dao.occurrences_in_window(start, end, type_ids, group_id, order_of_service_only):
            saved[(occurrence.series_id, occurrence.original_date)] = occurrence
            series_rows.setdefault(occurrence.series_id, occurrence.series)
        plan_counts = self.dao.plan_counts([row.id for row in saved.values()])
        template_counts = self.dao.template_counts(
            [row.id for row in series_rows.values() if row.event_type.has_order_of_service]
        )
        views = []
        for series in series_rows.values():
            schedule = recurrence.schedule_from_series(series)
            scheduled = set(recurrence.dates_between(schedule, start, end))
            for day in sorted(scheduled):
                occurrence = saved.pop((series.id, day), None)
                views.append(self._occurrence_view(series, day, occurrence, plan_counts, template_counts))
        for (series_id, day), occurrence in saved.items():
            series = series_rows[series_id]
            if occurrence.moved_to_date is None and not plan_counts.get(occurrence.id):
                continue
            views.append(self._occurrence_view(series, day, occurrence, plan_counts, template_counts))
        views = [view for view in views if start <= view.date <= end]
        if not include_cancelled:
            views = [view for view in views if view.status != "cancelled"]
        views.sort(key=lambda view: (view.date, view.all_day is False, view.start_time or datetime.time(), view.title))
        return views

    def get_occurrence(self, series_id, original_date):
        series = self._require_series(series_id)
        occurrence = self._existing_or_scheduled(series, original_date)
        return self._single_view(series, original_date, occurrence)

    def update_occurrence(self, series_id, original_date, payload: UpdateOccurrence):
        series = self._require_series(series_id)
        occurrence = self._existing_or_scheduled(series, original_date)
        changes = payload.model_dump(exclude_unset=True)
        scope = changes.pop("scope", "this")
        if not series.frequency:
            return self._update_once_off(series, changes)
        if scope == "this":
            return self._update_this(series, original_date, occurrence, changes)
        if "date" in changes:
            raise InvalidEventException("Moving a date only applies to 'this occurrence'")
        if scope == "all" or original_date <= series.start_date:
            self.update_series(series.id, UpdateEventSeries(**changes))
            refreshed = self.dao.get_series(series.id)
            return self._view_on_or_after(refreshed, original_date)
        return self._update_following(series, original_date, changes)

    def cancel_occurrence(self, series_id, original_date, reason=None):
        series = self._require_series(series_id)
        occurrence = self._materialise(series, original_date)
        occurrence.status = "cancelled"
        occurrence.cancel_reason = reason
        self.dao.save()
        return self._single_view(series, original_date, occurrence)

    def restore_occurrence(self, series_id, original_date):
        series = self._require_series(series_id)
        occurrence = self.dao.get_occurrence(series.id, original_date)
        if occurrence is None:
            raise NoOccurrenceException("That occurrence is not cancelled")
        occurrence.status = "scheduled"
        occurrence.cancel_reason = None
        self.dao.save()
        return self._single_view(series, original_date, occurrence)

    def cancel_range(self, series_id, payload: CancelRange):
        series = self._require_series(series_id)
        schedule = recurrence.schedule_from_series(series)
        days = recurrence.dates_between(schedule, payload.start, payload.end)
        cancelled = []
        for day in days:
            occurrence = self._materialise(series, day, commit=False)
            occurrence.status = "cancelled"
            occurrence.cancel_reason = payload.reason
            cancelled.append((day, occurrence))
        self.dao.save()
        return [self._single_view(series, day, occurrence) for day, occurrence in cancelled]

    def set_occurrence_image(self, series_id, original_date, image_id):
        series = self._require_series(series_id)
        occurrence = self._materialise(series, original_date)
        occurrence.image_id = image_id
        self.dao.save()
        return self._single_view(series, original_date, occurrence)

    def duplicate_occurrence(self, series_id, original_date, payload: DuplicateEvent, actor_user_id=None):
        """Copy one date into a new once-off event, order of service included."""
        series = self._require_series(series_id)
        occurrence = self._existing_or_scheduled(series, original_date)
        view = self._single_view(series, original_date, occurrence)
        copy = self._copy_series(series)
        copy.title = payload.title or view.title
        copy.description = view.description
        copy.image_id = view.image_id
        copy.start_date = payload.date
        copy.start_time = payload.start_time if payload.start_time is not None else view.start_time
        copy.end_time = payload.end_time if payload.end_time is not None else view.end_time
        copy.frequency = None
        copy.interval = 1
        copy.by_weekday = None
        copy.by_set_pos = None
        copy.until = None
        copy.created_by_user_id = actor_user_id
        if occurrence is not None and occurrence.location_override:
            copy.use_church_address = bool(occurrence.use_church_address)
            copy.address_id = occurrence.address_id
            copy.venue = occurrence.venue
            copy.online_url = occurrence.online_url
        created = self.dao.add_series(copy)
        if occurrence is not None and occurrence.plan_initialised:
            items = [self._clone_item(item) for item in self.dao.occurrence_items(occurrence.id)]
            self.dao.replace_template(created.id, items)
        else:
            self._copy_template(series.id, created.id)
        self.dao.save()
        return self.get_occurrence(created.id, payload.date)

    # Order of service

    def get_template(self, series_id):
        series = self._require_series(series_id)
        self._require_order_of_service(series)
        return [self._item_view(item) for item in self.dao.template_items(series.id)]

    def replace_template(self, series_id, payload: TemplateInput):
        series = self._require_series(series_id)
        self._require_order_of_service(series)
        self.dao.replace_template(series.id, [self._new_item(item) for item in payload.items])
        self.dao.save()
        return self.get_template(series.id)

    def get_plan(self, series_id, original_date):
        series = self._require_series(series_id)
        self._require_order_of_service(series)
        occurrence = self._existing_or_scheduled(series, original_date)
        return self._plan_view(series, original_date, occurrence)

    def save_plan(self, series_id, original_date, payload: PlanInput):
        series = self._require_series(series_id)
        self._require_order_of_service(series)
        occurrence = self._materialise(series, original_date)
        self.dao.replace_occurrence_items(occurrence.id, [self._new_item(item) for item in payload.items])
        occurrence.plan_status = payload.status
        occurrence.plan_initialised = True
        self.dao.save()
        return self._plan_view(series, original_date, occurrence)

    def reset_plan(self, series_id, original_date):
        series = self._require_series(series_id)
        self._require_order_of_service(series)
        occurrence = self.dao.get_occurrence(series.id, original_date)
        if occurrence is not None:
            self.dao.replace_occurrence_items(occurrence.id, [])
            occurrence.plan_initialised = False
            occurrence.plan_status = "draft"
            self.dao.save()
        return self._plan_view(series, original_date, occurrence)

    # Views

    def series_view(self, series):
        schedule = recurrence.schedule_from_series(series)
        recurrence_view = None
        if schedule.is_recurring:
            recurrence_view = RecurrenceView(
                frequency=schedule.frequency,
                interval=schedule.interval,
                weekdays=list(schedule.weekdays),
                positions=list(schedule.positions),
                until=schedule.until,
                label=recurrence.describe(schedule),
            )
        return SeriesView(
            id=series.id,
            title=series.title,
            description=series.description,
            event_type=type_view(series.event_type),
            group_id=series.group_id,
            group_name=series.group.name if series.group else None,
            image_id=series.image_id,
            location=self._series_location(series),
            start_date=series.start_date,
            start_time=series.start_time,
            end_time=series.end_time,
            all_day=bool(series.all_day),
            recurrence=recurrence_view,
            schedule_label=recurrence.describe(schedule),
            next_date=recurrence.next_date(schedule, datetime.date.today()),
            status=series.status,
        )

    def _single_view(self, series, original_date, occurrence):
        plan_counts = self.dao.plan_counts([occurrence.id]) if occurrence is not None and occurrence.id else {}
        template_counts = self.dao.template_counts([series.id]) if series.event_type.has_order_of_service else {}
        return self._occurrence_view(series, original_date, occurrence, plan_counts, template_counts)

    def _occurrence_view(self, series, original_date, occurrence, plan_counts, template_counts):
        overridden = []
        title = series.title
        description = series.description
        image_id = series.image_id
        day = original_date
        start_time = series.start_time
        end_time = series.end_time
        location = self._series_location(series)
        status = "scheduled"
        cancel_reason = None
        if occurrence is not None:
            if occurrence.title:
                title = occurrence.title
                overridden.append("title")
            if occurrence.description:
                description = occurrence.description
                overridden.append("description")
            if occurrence.image_id:
                image_id = occurrence.image_id
                overridden.append("image")
            if occurrence.moved_to_date:
                day = occurrence.moved_to_date
                overridden.append("date")
            if occurrence.start_time:
                start_time = occurrence.start_time
                overridden.append("start_time")
            if occurrence.end_time:
                end_time = occurrence.end_time
                overridden.append("end_time")
            if occurrence.location_override:
                location = LocationView(
                    use_church_address=bool(occurrence.use_church_address),
                    address=self._church_address_view() if occurrence.use_church_address else address_view(occurrence.address),
                    venue=occurrence.venue,
                    online_url=occurrence.online_url,
                )
                overridden.append("location")
            status = occurrence.status
            cancel_reason = occurrence.cancel_reason
        plan_state = None
        plan_item_count = 0
        if series.event_type.has_order_of_service:
            if occurrence is not None and occurrence.plan_initialised:
                plan_state = occurrence.plan_status or "draft"
                plan_item_count = plan_counts.get(occurrence.id, 0)
            else:
                plan_state = "not_started"
                plan_item_count = template_counts.get(series.id, 0)
        return OccurrenceView(
            key=occurrence_key(series.id, original_date),
            id=occurrence.id if occurrence is not None else None,
            series_id=series.id,
            original_date=original_date,
            date=day,
            start_time=None if series.all_day else start_time,
            end_time=None if series.all_day else end_time,
            all_day=bool(series.all_day),
            title=title,
            description=description,
            event_type=type_view(series.event_type),
            group_id=series.group_id,
            group_name=series.group.name if series.group else None,
            image_id=image_id,
            location=location,
            is_recurring=bool(series.frequency),
            schedule_label=recurrence.describe(recurrence.schedule_from_series(series)),
            status=status,
            cancel_reason=cancel_reason,
            overridden_fields=overridden,
            plan_state=plan_state,
            plan_item_count=plan_item_count,
        )

    def _plan_view(self, series, original_date, occurrence):
        if occurrence is not None and occurrence.plan_initialised:
            items = self.dao.occurrence_items(occurrence.id)
            status = occurrence.plan_status or "draft"
            initialised = True
        else:
            items = self.dao.template_items(series.id)
            status = "draft"
            initialised = False
        view = self._single_view(series, original_date, occurrence)
        item_views = []
        cursor = None
        if view.start_time is not None:
            cursor = datetime.datetime.combine(view.date, view.start_time)
        total = 0
        for item in items:
            item_view = self._item_view(item)
            if cursor is not None:
                item_view.planned_start = cursor.time()
            minutes = item.duration_minutes or 0
            total += minutes
            if cursor is not None:
                cursor += datetime.timedelta(minutes=minutes)
            item_views.append(item_view)
        return PlanView(occurrence=view, initialised=initialised, status=status, total_minutes=total, items=item_views)

    def _item_view(self, item):
        song = item.song
        return PlanItemView(
            id=item.id,
            position=item.position,
            item_type=item.item_type,
            title=item.title,
            song_id=item.song_id,
            song_key=item.song_key,
            scripture_reference=item.scripture_reference,
            person_id=item.person_id,
            person_name=item.person_name,
            duration_minutes=item.duration_minutes,
            notes=item.notes,
            song_name=song.name if song else None,
            song_ccli_number=song.ccli_number if song else None,
            song_default_key=song.song_key if song else None,
            person_display_name=_person_name(item.person) or item.person_name,
        )

    # Internals

    def _update_once_off(self, series, changes):
        if "date" in changes:
            changes["start_date"] = changes.pop("date")
        previous_start = series.start_date
        self._apply_series_changes(series, changes)
        if series.start_date != previous_start and not series.frequency:
            saved = self.dao.get_occurrence(series.id, previous_start)
            if saved is not None:
                saved.original_date = series.start_date
                saved.moved_to_date = None
        self._drop_unscheduled(series)
        self.dao.save()
        refreshed = self.dao.get_series(series.id)
        return self._view_on_or_after(refreshed, refreshed.start_date)

    def _update_this(self, series, original_date, occurrence, changes):
        for blocked in ("event_type_id", "group_id", "recurrence", "all_day"):
            if blocked in changes:
                raise InvalidEventException(f"'{blocked}' applies to the whole series, not one occurrence")
        occurrence = occurrence or self._materialise(series, original_date, commit=False)
        if "title" in changes:
            occurrence.title = (changes["title"] or "").strip() or None
        if "description" in changes:
            occurrence.description = changes["description"] or None
        if "date" in changes:
            new_date = changes["date"]
            occurrence.moved_to_date = None if new_date in (None, original_date) else new_date
        if "start_time" in changes:
            occurrence.start_time = changes["start_time"]
        if "end_time" in changes:
            occurrence.end_time = changes["end_time"]
        start = occurrence.start_time or series.start_time
        end = occurrence.end_time or series.end_time
        if start and end and end <= start:
            raise InvalidEventException("End time must be after the start time")
        if "location" in changes:
            location = changes["location"]
            if location is None:
                occurrence.location_override = False
                occurrence.use_church_address = None
                occurrence.address_id = None
                occurrence.venue = None
                occurrence.online_url = None
            else:
                self._require_address(location.get("address_id"))
                occurrence.location_override = True
                occurrence.use_church_address = bool(location.get("use_church_address"))
                occurrence.address_id = location.get("address_id")
                occurrence.venue = location.get("venue")
                occurrence.online_url = location.get("online_url")
        if occurrence.id is None:
            self.dao.add_occurrence(occurrence)
        else:
            self.dao.save()
        return self._single_view(series, original_date, self.dao.get_occurrence(series.id, original_date))

    def _update_following(self, series, original_date, changes):
        copy = self._copy_series(series)
        copy.start_date = original_date
        series.until = original_date - datetime.timedelta(days=1)
        self._apply_series_changes(copy, changes, keep_start=True)
        created = self.dao.add_series(copy)
        self._copy_template(series.id, created.id)
        for occurrence in self.dao.occurrences_for_series(series.id, from_date=original_date):
            occurrence.series_id = created.id
        self.dao.flush()
        self._clear_overrides(self.dao.occurrences_for_series(created.id), changes)
        self._drop_unscheduled(created)
        self.dao.save()
        refreshed = self.dao.get_series(created.id)
        return self._view_on_or_after(refreshed, original_date)

    def _view_on_or_after(self, series, day):
        schedule = recurrence.schedule_from_series(series)
        target = day if recurrence.occurs_on(schedule, day) else recurrence.next_date(schedule, day)
        if target is None:
            target = series.start_date
        occurrence = self.dao.get_occurrence(series.id, target)
        return self._single_view(series, target, occurrence)

    def _apply_series_changes(self, series, changes, keep_start=False):
        if "event_type_id" in changes:
            series.event_type_id = self._require_type(changes["event_type_id"]).id
        if "group_id" in changes:
            self._require_group(changes["group_id"])
            series.group_id = changes["group_id"]
        if "title" in changes:
            title = (changes["title"] or "").strip()
            if not title:
                raise InvalidEventException("An event needs a title")
            series.title = title
        if "description" in changes:
            series.description = changes["description"]
        if "all_day" in changes and changes["all_day"] is not None:
            series.all_day = changes["all_day"]
        if "start_time" in changes:
            series.start_time = changes["start_time"]
        if "end_time" in changes:
            series.end_time = changes["end_time"]
        if series.all_day:
            series.start_time = None
            series.end_time = None
        if series.start_time and series.end_time and series.end_time <= series.start_time:
            raise InvalidEventException("End time must be after the start time")
        if "location" in changes and changes["location"] is not None:
            location = LocationInput(**changes["location"])
            self._require_address(location.address_id)
            self._apply_location(series, location)
        if "start_date" in changes and changes["start_date"] is not None and not keep_start:
            series.start_date = changes["start_date"]
        if "recurrence" in changes:
            raw = changes["recurrence"]
            schedule = self._schedule(series.start_date, RecurrenceInput(**raw) if raw else None)
            self._apply_schedule(series, schedule)
        else:
            self._validate_series(series)

    def _clear_overrides(self, occurrences, changes):
        for occurrence in occurrences:
            if "title" in changes:
                occurrence.title = None
            if "description" in changes:
                occurrence.description = None
            if "start_time" in changes:
                occurrence.start_time = None
            if "end_time" in changes:
                occurrence.end_time = None
            if "location" in changes:
                occurrence.location_override = False
                occurrence.use_church_address = None
                occurrence.address_id = None
                occurrence.venue = None
                occurrence.online_url = None

    def _drop_unscheduled(self, series):
        """Remove saved dates the schedule no longer produces, unless they hold an order of service."""
        schedule = recurrence.schedule_from_series(series)
        occurrences = self.dao.occurrences_for_series(series.id)
        if not occurrences:
            return
        counts = self.dao.plan_counts([row.id for row in occurrences])
        for occurrence in occurrences:
            if recurrence.occurs_on(schedule, occurrence.original_date):
                continue
            if counts.get(occurrence.id) or occurrence.moved_to_date:
                continue
            self.dao.delete_occurrence(occurrence)

    def _existing_or_scheduled(self, series, original_date):
        occurrence = self.dao.get_occurrence(series.id, original_date)
        if occurrence is not None:
            return occurrence
        if not recurrence.occurs_on(recurrence.schedule_from_series(series), original_date):
            raise NoOccurrenceException(f"'{series.title}' does not happen on {original_date.isoformat()}")
        return None

    def _materialise(self, series, original_date, commit=True):
        occurrence = self._existing_or_scheduled(series, original_date)
        if occurrence is not None:
            return occurrence
        occurrence = models.EventOccurrence(series_id=series.id, original_date=original_date, status="scheduled")
        if commit:
            return self.dao.add_occurrence(occurrence)
        self.dao.db.add(occurrence)
        return occurrence

    def _schedule(self, start_date, rule: RecurrenceInput | None):
        raw = recurrence.Schedule(
            start_date=start_date,
            frequency=rule.frequency if rule else None,
            interval=rule.interval if rule else 1,
            weekdays=tuple(rule.weekdays) if rule else (),
            positions=tuple(rule.positions) if rule else (),
            until=rule.until if rule else None,
        )
        try:
            return recurrence.validate(raw)
        except recurrence.InvalidRecurrence as exc:
            raise InvalidEventException(str(exc))

    def _apply_schedule(self, series, schedule):
        series.start_date = schedule.start_date
        series.frequency = schedule.frequency
        series.interval = schedule.interval
        series.by_weekday = ",".join(schedule.weekdays) or None
        series.by_set_pos = ",".join(str(value) for value in schedule.positions) or None
        series.until = schedule.until

    def _validate_series(self, series):
        self._apply_schedule(series, self._schedule_from_columns(series))

    def _schedule_from_columns(self, series):
        current = recurrence.schedule_from_series(series)
        try:
            return recurrence.validate(current)
        except recurrence.InvalidRecurrence as exc:
            raise InvalidEventException(str(exc))

    def _apply_location(self, series, location: LocationInput):
        series.use_church_address = location.use_church_address
        series.address_id = None if location.use_church_address else location.address_id
        series.venue = location.venue
        series.online_url = location.online_url

    def _series_location(self, series):
        return LocationView(
            use_church_address=bool(series.use_church_address),
            address=self._church_address_view() if series.use_church_address else address_view(series.address),
            venue=series.venue,
            online_url=series.online_url,
        )

    def _church_address_view(self):
        if not self._church_address_loaded:
            self._church_address = address_view(self.dao.church_address())
            self._church_address_loaded = True
        return self._church_address

    def _copy_series(self, source):
        return models.EventSeries(
            event_type_id=source.event_type_id,
            group_id=source.group_id,
            title=source.title,
            description=source.description,
            image_id=source.image_id,
            use_church_address=source.use_church_address,
            address_id=source.address_id,
            venue=source.venue,
            online_url=source.online_url,
            start_date=source.start_date,
            start_time=source.start_time,
            end_time=source.end_time,
            all_day=source.all_day,
            frequency=source.frequency,
            interval=source.interval,
            by_weekday=source.by_weekday,
            by_set_pos=source.by_set_pos,
            until=source.until,
            status="active",
            created_by_user_id=source.created_by_user_id,
        )

    def _copy_template(self, source_series_id, target_series_id):
        items = [self._clone_item(item) for item in self.dao.template_items(source_series_id)]
        if items:
            self.dao.replace_template(target_series_id, items)

    def _clone_item(self, item):
        return models.ServicePlanItem(
            item_type=item.item_type,
            title=item.title,
            song_id=item.song_id,
            song_key=item.song_key,
            scripture_reference=item.scripture_reference,
            person_id=item.person_id,
            person_name=item.person_name,
            duration_minutes=item.duration_minutes,
            notes=item.notes,
        )

    def _new_item(self, item: PlanItemInput):
        if item.song_id is not None and not self.dao.song_exists(item.song_id):
            raise InvalidEventException(f"No song with ID {item.song_id}")
        if item.person_id is not None and self.dao.db.get(Person, item.person_id) is None:
            raise InvalidEventException(f"No person with ID {item.person_id}")
        return models.ServicePlanItem(**item.model_dump())

    def _require_type(self, type_id, allow_inactive=False):
        event_type = self.dao.get_type(type_id)
        if event_type is None or (not allow_inactive and not event_type.active):
            raise NoEventTypeException("Event type does not exist")
        return event_type

    def _require_series(self, series_id):
        series = self.dao.get_series(series_id)
        if series is None:
            raise NoSeriesException("Event does not exist")
        return series

    def _require_group(self, group_id):
        if group_id is None:
            return
        if self.dao.db.get(Group, group_id) is None:
            raise InvalidEventException(f"No group with ID {group_id}")

    def _require_address(self, address_id):
        if address_id is None:
            return
        if self.dao.db.get(Address, address_id) is None:
            raise InvalidEventException(f"No address with ID {address_id}")

    def _require_order_of_service(self, series):
        if not series.event_type.has_order_of_service:
            raise NoOrderOfServiceException(f"'{series.event_type.name}' events do not have an order of service")
