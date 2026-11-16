import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.church.models.database.models import Church
from src.app.dashboard.services.dashboardService import (
    WIDGET_IDS,
    DashboardLayoutInput,
    DashboardService,
    WidgetSetting,
)
from src.app.database import Base
from src.app.events import recurrence
from src.app.events.daos.eventDAO import EventDAO
from src.app.events.models.database import models as event_models
from src.app.events.models.events import (
    CancelRange,
    CreateEvent,
    DuplicateEvent,
    EventTypeInput,
    LocationInput,
    PlanInput,
    PlanItemInput,
    RecurrenceInput,
    TemplateInput,
    UpdateOccurrence,
)
from src.app.events.services.eventService import (
    EventService,
    InvalidEventException,
    NoOccurrenceException,
    NoOrderOfServiceException,
)
from src.app.events.services.songUsageService import SongUsageService
from src.app.groups.models.database.models import Group, GroupMembership
from src.app.model_registry import import_all_models
from src.app.people.models.database.models import Address, Person
from src.app.seed import EVENT_TYPES, ReferenceSeed
from src.app.users.models.database.models import User
from src.app.users.models.login import TokenData
from src.app.worship.models.database.models import Song

D = datetime.date
T = datetime.time


@pytest.fixture()
def db():
    import_all_models()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    ReferenceSeed(session).seed()
    yield session
    session.close()


@pytest.fixture()
def events(db):
    return EventService(EventDAO(db))


def _type(db, name):
    return db.query(event_models.EventType).filter(event_models.EventType.name == name).one()


def _sunday_service(events, db, **extra):
    payload = dict(
        event_type_id=_type(db, "Sunday Service").id,
        title="Morning Service",
        start_date=D(2026, 11, 1),
        start_time=T(9, 0),
        end_time=T(10, 30),
        recurrence=RecurrenceInput(frequency="weekly", weekdays=["SU"]),
    )
    payload.update(extra)
    return events.create(CreateEvent(**payload))


def _dates(views):
    return [view.date for view in views]


# Recurrence

def test_recurrence_patterns():
    first_and_third_monday = recurrence.validate(recurrence.Schedule(
        start_date=D(2026, 11, 1), frequency="monthly", weekdays=("MO",), positions=(1, 3),
    ))
    assert recurrence.dates_between(first_and_third_monday, D(2026, 11, 1), D(2026, 12, 31)) == [
        D(2026, 11, 2), D(2026, 11, 16), D(2026, 12, 7), D(2026, 12, 21),
    ]
    assert recurrence.describe(first_and_third_monday) == "1st and 3rd Monday of every month"

    last_friday = recurrence.validate(recurrence.Schedule(
        start_date=D(2026, 11, 1), frequency="monthly", weekdays=("FR",), positions=(-1,),
    ))
    assert recurrence.dates_between(last_friday, D(2026, 11, 1), D(2026, 12, 31)) == [D(2026, 11, 27), D(2026, 12, 25)]

    fortnightly = recurrence.validate(recurrence.Schedule(start_date=D(2026, 11, 3), frequency="weekly", interval=2))
    assert fortnightly.weekdays == ("TU",)
    assert recurrence.dates_between(fortnightly, D(2026, 11, 1), D(2026, 11, 30)) == [D(2026, 11, 3), D(2026, 11, 17)]
    assert recurrence.describe(fortnightly) == "Every 2 weeks on Tuesday"

    yearly = recurrence.validate(recurrence.Schedule(
        start_date=D(2026, 12, 25), frequency="yearly", until=D(2028, 1, 1),
    ))
    assert recurrence.dates_between(yearly, D(2026, 1, 1), D(2030, 1, 1)) == [D(2026, 12, 25), D(2027, 12, 25)]

    with pytest.raises(recurrence.InvalidRecurrence):
        recurrence.validate(recurrence.Schedule(start_date=D(2026, 11, 1), frequency="monthly", weekdays=("MO",)))


def test_seeded_event_types_and_flags(db, events):
    types = {view.name: view for view in events.list_types()}
    assert list(types) == [name for name, *_ in EVENT_TYPES]
    assert types["Sunday Service"].has_order_of_service and types["Sunday Service"].tracks_attendance
    assert types["Bible Study"].tracks_attendance and not types["Bible Study"].has_order_of_service
    assert not types["Social / Community"].tracks_attendance
    ReferenceSeed(db).seed()
    assert len(events.list_types()) == len(EVENT_TYPES)


def test_type_delete_deactivates_when_in_use(db, events):
    created = events.create_type(EventTypeInput(name="Book club"))
    assert events.delete_type(created.id) is None
    _sunday_service(events, db)
    in_use = events.delete_type(_type(db, "Sunday Service").id)
    assert in_use.active is False


# Calendar and occurrences

def test_weekly_series_lists_occurrences_with_church_location(db, events):
    church_address = Address(street="1 Church Street", city="Cape Town")
    db.add(church_address)
    db.flush()
    db.add(Church(created=datetime.datetime.now(), address_id=church_address.id))
    db.commit()

    series = _sunday_service(events, db)
    assert series.schedule_label == "Weekly on Sunday"
    assert series.location.use_church_address
    views = events.list_occurrences(D(2026, 11, 1), D(2026, 11, 30))
    assert _dates(views) == [D(2026, 11, 1), D(2026, 11, 8), D(2026, 11, 15), D(2026, 11, 22), D(2026, 11, 29)]
    assert views[0].location.address.street == "1 Church Street"
    assert views[0].plan_state == "not_started"
    assert views[0].id is None


def test_bible_study_defaults_to_address_and_once_off(db, events):
    address = Address(street="12 Oak Lane", city="Durbanville")
    db.add(address)
    db.commit()
    study = events.create(CreateEvent(
        event_type_id=_type(db, "Bible Study").id,
        title="Tuesday study",
        start_date=D(2026, 11, 3),
        start_time=T(19, 0),
        location=LocationInput(address_id=address.id, online_url="https://meet.example/study"),
        recurrence=RecurrenceInput(frequency="weekly", weekdays=["TU"]),
    ))
    assert study.location.address.street == "12 Oak Lane"
    once = events.create(CreateEvent(event_type_id=_type(db, "Social / Community").id, title="Braai", start_date=D(2026, 11, 7)))
    assert once.schedule_label == "Once-off"
    assert not once.location.use_church_address
    views = events.list_occurrences(D(2026, 11, 1), D(2026, 11, 9))
    assert [(view.title, view.date) for view in views] == [("Tuesday study", D(2026, 11, 3)), ("Braai", D(2026, 11, 7))]
    with pytest.raises(NoOccurrenceException):
        events.get_occurrence(study.id, D(2026, 11, 4))


def test_this_occurrence_override_and_move(db, events):
    series = _sunday_service(events, db)
    moved = events.update_occurrence(series.id, D(2026, 11, 15), UpdateOccurrence(
        title="Baptism Sunday", start_time=T(10, 0), end_time=T(12, 0), date=D(2026, 11, 14),
    ))
    assert moved.title == "Baptism Sunday"
    assert moved.date == D(2026, 11, 14)
    assert set(moved.overridden_fields) == {"title", "date", "start_time", "end_time"}
    views = events.list_occurrences(D(2026, 11, 8), D(2026, 11, 22))
    assert [(view.date, view.title) for view in views] == [
        (D(2026, 11, 8), "Morning Service"),
        (D(2026, 11, 14), "Baptism Sunday"),
        (D(2026, 11, 22), "Morning Service"),
    ]
    with pytest.raises(InvalidEventException):
        events.update_occurrence(series.id, D(2026, 11, 22), UpdateOccurrence(
            recurrence=RecurrenceInput(frequency="weekly", weekdays=["SA"]),
        ))


def test_all_scope_changes_series_and_clears_matching_overrides(db, events):
    series = _sunday_service(events, db)
    events.update_occurrence(series.id, D(2026, 11, 15), UpdateOccurrence(title="Special", start_time=T(10, 0)))
    events.update_occurrence(series.id, D(2026, 11, 22), UpdateOccurrence(scope="all", start_time=T(9, 30)))
    views = events.list_occurrences(D(2026, 11, 1), D(2026, 11, 30))
    assert {view.start_time for view in views} == {T(9, 30)}
    assert [view.title for view in views if view.date == D(2026, 11, 15)] == ["Special"]


def test_following_scope_splits_series(db, events):
    series = _sunday_service(events, db)
    events.update_occurrence(series.id, D(2026, 11, 22), UpdateOccurrence(title="Rename later"))
    result = events.update_occurrence(series.id, D(2026, 11, 15), UpdateOccurrence(
        scope="following", title="Morning Worship", start_time=T(9, 30),
    ))
    assert result.series_id != series.id
    assert result.date == D(2026, 11, 15)
    old = events.get_series(series.id)
    assert old.recurrence.until == D(2026, 11, 14)
    views = events.list_occurrences(D(2026, 11, 1), D(2026, 11, 29))
    assert [(view.date, view.title, view.start_time) for view in views] == [
        (D(2026, 11, 1), "Morning Service", T(9, 0)),
        (D(2026, 11, 8), "Morning Service", T(9, 0)),
        (D(2026, 11, 15), "Morning Worship", T(9, 30)),
        (D(2026, 11, 22), "Morning Worship", T(9, 30)),
        (D(2026, 11, 29), "Morning Worship", T(9, 30)),
    ]


def test_pattern_change_drops_unscheduled_saved_dates_but_keeps_plans(db, events):
    series = _sunday_service(events, db)
    events.cancel_occurrence(series.id, D(2026, 11, 8), "Camp")
    events.save_plan(series.id, D(2026, 11, 15), PlanInput(items=[PlanItemInput(item_type="prayer", duration_minutes=5)]))
    events.update_occurrence(series.id, D(2026, 11, 1), UpdateOccurrence(
        scope="all", recurrence=RecurrenceInput(frequency="weekly", interval=2, weekdays=["SU"]),
    ))
    views = events.list_occurrences(D(2026, 11, 1), D(2026, 11, 30))
    assert _dates(views) == [D(2026, 11, 1), D(2026, 11, 15), D(2026, 11, 29)]
    assert EventDAO(db).get_occurrence(series.id, D(2026, 11, 8)) is None


def test_once_off_date_change_keeps_saved_details(db, events):
    special = events.create(CreateEvent(
        event_type_id=_type(db, "Special Service").id, title="Good Friday", start_date=D(2027, 3, 26), start_time=T(9, 0),
    ))
    events.save_plan(special.id, D(2027, 3, 26), PlanInput(items=[PlanItemInput(item_type="reading", scripture_reference="John 19")]))
    moved = events.update_occurrence(special.id, D(2027, 3, 26), UpdateOccurrence(date=D(2027, 3, 25)))
    assert moved.date == D(2027, 3, 25)
    plan = events.get_plan(special.id, D(2027, 3, 25))
    assert plan.initialised and plan.items[0].scripture_reference == "John 19"


def test_cancel_restore_and_bulk_cancel(db, events):
    series = _sunday_service(events, db)
    cancelled = events.cancel_occurrence(series.id, D(2026, 11, 8), "Church camp")
    assert cancelled.status == "cancelled" and cancelled.cancel_reason == "Church camp"
    assert events.restore_occurrence(series.id, D(2026, 11, 8)).status == "scheduled"

    bulk = events.cancel_range(series.id, CancelRange(start=D(2026, 12, 20), end=D(2027, 1, 3), reason="Holidays"))
    assert _dates(bulk) == [D(2026, 12, 20), D(2026, 12, 27), D(2027, 1, 3)]
    views = events.list_occurrences(D(2026, 12, 13), D(2027, 1, 10))
    assert [view.status for view in views] == ["scheduled", "cancelled", "cancelled", "cancelled", "scheduled"]
    assert len(events.list_occurrences(D(2026, 12, 13), D(2027, 1, 10), include_cancelled=False)) == 2


def test_duplicate_occurrence_to_next_year_copies_plan(db, events):
    special = events.create(CreateEvent(
        event_type_id=_type(db, "Special Service").id, title="Christmas Day", start_date=D(2026, 12, 25), start_time=T(9, 0),
    ))
    events.save_plan(special.id, D(2026, 12, 25), PlanInput(items=[PlanItemInput(item_type="reading", scripture_reference="Luke 2")]))
    copy = events.duplicate_occurrence(special.id, D(2026, 12, 25), DuplicateEvent(date=D(2027, 12, 25)))
    assert copy.series_id != special.id
    assert copy.date == D(2027, 12, 25) and copy.title == "Christmas Day"
    plan = events.get_plan(copy.series_id, D(2027, 12, 25))
    assert not plan.initialised
    assert plan.items[0].scripture_reference == "Luke 2"

    series = _sunday_service(events, db)
    duplicated = events.duplicate_series(series.id, DuplicateEvent(date=D(2026, 11, 2), title="Evening Service", start_time=T(18, 0)))
    assert duplicated.title == "Evening Service" and duplicated.start_time == T(18, 0)


# Order of service

def test_template_plan_and_planned_times(db, events):
    song = Song(id=1, name="Amazing Grace", code="AG1", ccli_number="22025", song_key="G")
    preacher = Person(first_name="Ada", last_name="Lovelace", preferred_name="Addie")
    db.add_all([song, preacher])
    db.commit()
    series = _sunday_service(events, db)
    events.replace_template(series.id, TemplateInput(items=[
        PlanItemInput(item_type="song", song_id=song.id, duration_minutes=5),
        PlanItemInput(item_type="sermon", title="Grace", person_id=preacher.id, duration_minutes=30),
    ]))
    preview = events.get_plan(series.id, D(2026, 11, 15))
    assert not preview.initialised
    assert [item.planned_start for item in preview.items] == [T(9, 0), T(9, 5)]
    assert preview.items[0].song_name == "Amazing Grace"
    assert preview.items[1].person_display_name == "Addie Lovelace"
    assert events.get_occurrence(series.id, D(2026, 11, 15)).plan_item_count == 2

    saved = events.save_plan(series.id, D(2026, 11, 15), PlanInput(status="final", items=[
        PlanItemInput(item_type="song", song_id=song.id, song_key="A", duration_minutes=4),
        PlanItemInput(item_type="reading", scripture_reference="Eph 2:1-10", person_name="Guest reader", duration_minutes=3),
    ]))
    assert saved.initialised and saved.status == "final" and saved.total_minutes == 7
    assert saved.items[1].person_display_name == "Guest reader"
    assert events.get_occurrence(series.id, D(2026, 11, 15)).plan_state == "final"
    assert len(events.get_template(series.id)) == 2

    reset = events.reset_plan(series.id, D(2026, 11, 15))
    assert not reset.initialised and len(reset.items) == 2

    with pytest.raises(InvalidEventException):
        events.save_plan(series.id, D(2026, 11, 22), PlanInput(items=[PlanItemInput(item_type="song", song_id=999)]))


def test_order_of_service_only_for_service_types(db, events):
    study = events.create(CreateEvent(event_type_id=_type(db, "Bible Study").id, title="Study", start_date=D(2026, 11, 3)))
    with pytest.raises(NoOrderOfServiceException):
        events.get_plan(study.id, D(2026, 11, 3))
    assert events.get_occurrence(study.id, D(2026, 11, 3)).plan_state is None


def test_song_usage_and_ccli_report(db, events):
    grace = Song(id=1, name="Amazing Grace", code="AG1", ccli_number="22025")
    cornerstone = Song(id=2, name="Cornerstone", code="CS1", ccli_number="6158927")
    db.add_all([grace, cornerstone])
    db.commit()
    series = _sunday_service(events, db)
    for day in (D(2026, 11, 1), D(2026, 11, 8)):
        events.save_plan(series.id, day, PlanInput(items=[PlanItemInput(item_type="song", song_id=grace.id)]))
    events.save_plan(series.id, D(2026, 11, 15), PlanInput(items=[PlanItemInput(item_type="song", song_id=cornerstone.id)]))
    events.save_plan(series.id, D(2026, 11, 22), PlanInput(items=[PlanItemInput(item_type="song", song_id=cornerstone.id)]))
    events.cancel_occurrence(series.id, D(2026, 11, 22))

    usage = SongUsageService(EventDAO(db))
    rows = usage.usage(D(2026, 11, 1), D(2026, 11, 30))
    assert [(row.name, row.times_used, row.last_used) for row in rows] == [
        ("Amazing Grace", 2, D(2026, 11, 8)),
        ("Cornerstone", 1, D(2026, 11, 15)),
    ]
    detail = usage.detail(grace.id, today=D(2026, 11, 10))
    assert detail.times_used_last_12_months == 2 and detail.last_used == D(2026, 11, 8)
    csv_text = usage.ccli_csv(D(2026, 11, 1), D(2026, 11, 30))
    assert csv_text.splitlines() == [
        "Song,CCLI number,Times used,Last used",
        "Amazing Grace,22025,2,2026-11-08",
        "Cornerstone,6158927,1,2026-11-15",
    ]


def test_group_filter_and_window_limit(db, events):
    group = Group(name="Tuesday study", status="active")
    db.add(group)
    db.commit()
    events.create(CreateEvent(event_type_id=_type(db, "Bible Study").id, title="Study", group_id=group.id,
                              start_date=D(2026, 11, 3), recurrence=RecurrenceInput(frequency="weekly")))
    _sunday_service(events, db)
    views = events.list_occurrences(D(2026, 11, 1), D(2026, 11, 14), group_id=group.id)
    assert [(view.title, view.group_name) for view in views] == [("Study", "Tuesday study"), ("Study", "Tuesday study")]
    services = events.list_occurrences(D(2026, 11, 1), D(2026, 11, 14), order_of_service_only=True)
    assert {view.title for view in services} == {"Morning Service"}
    with pytest.raises(InvalidEventException):
        events.list_occurrences(D(2026, 1, 1), D(2027, 6, 1))


# Dashboard

def test_dashboard_layout_defaults_save_and_new_widgets(db):
    user = User(email="staff@example.org", first_name="Staff", last_name="Member", password="x")
    db.add(user)
    db.commit()
    dashboard = DashboardService(db)
    assert dashboard.user_id_for(TokenData(username="Staff@Example.org")) == user.id
    assert dashboard.user_id_for(TokenData(username="nobody@example.org")) is None
    default = dashboard.layout(user.id)
    assert not default.customised
    assert [widget.id for widget in default.widgets] == list(WIDGET_IDS)

    saved = dashboard.save_layout(user.id, DashboardLayoutInput(widgets=[
        WidgetSetting(id="top_songs", visible=True),
        WidgetSetting(id="this_week", visible=False),
        WidgetSetting(id="not_a_widget", visible=True),
    ]))
    assert saved.customised
    assert [widget.id for widget in saved.widgets][:2] == ["top_songs", "this_week"]
    assert saved.widgets[1].visible is False
    assert {widget.id for widget in saved.widgets} == set(WIDGET_IDS)
    assert not dashboard.reset_layout(user.id).customised


def test_dashboard_summary_counts(db):
    ada = Person(first_name="Ada", last_name="Lovelace", lifecycle_status="member", email="ada@example.org",
                 registered_date=datetime.datetime.now())
    charles = Person(first_name="Charles", last_name="Babbage", lifecycle_status="visitor")
    db.add_all([ada, charles])
    group = Group(name="Study", status="active")
    db.add(group)
    db.flush()
    db.add(GroupMembership(group_id=group.id, person_id=ada.id, status="active"))
    db.commit()
    summary = DashboardService(db).summary()
    assert summary.people_total == 2
    assert summary.people_new_last_30_days == 1
    assert {row.status: row.count for row in summary.people_by_status} == {"member": 1, "visitor": 1}
    assert summary.people_without_email == 1
    assert summary.people_without_mobile == 2
    assert summary.people_without_group == 1
    assert summary.groups_active == 1 and summary.group_memberships_active == 1
