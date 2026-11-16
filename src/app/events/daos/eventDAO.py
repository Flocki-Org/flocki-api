from datetime import datetime

from fastapi import Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from src.app.church.models.database.models import Church
from src.app.database import SessionLocal, get_db
from src.app.events.models.database import models
from src.app.worship.models.database.models import Song


def effective_date_column():
    return func.coalesce(models.EventOccurrence.moved_to_date, models.EventOccurrence.original_date)


class EventDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    # Event types

    def list_types(self, include_inactive=False):
        query = self.db.query(models.EventType).order_by(models.EventType.display_order.asc(), models.EventType.name.asc())
        if not include_inactive:
            query = query.filter(models.EventType.active.is_(True))
        return query.all()

    def get_type(self, type_id):
        return self.db.query(models.EventType).filter(models.EventType.id == type_id).first()

    def get_type_by_name(self, name):
        return self.db.query(models.EventType).filter(func.lower(models.EventType.name) == name.lower()).first()

    def add_type(self, event_type):
        self.db.add(event_type)
        self.db.commit()
        self.db.refresh(event_type)
        return event_type

    def save_type(self, event_type):
        event_type.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(event_type)
        return event_type

    def type_in_use(self, type_id):
        return self.db.query(models.EventSeries.id).filter(models.EventSeries.event_type_id == type_id).first() is not None

    def delete_type(self, event_type):
        self.db.delete(event_type)
        self.db.commit()

    # Series

    def _series_options(self):
        return [
            joinedload(models.EventSeries.event_type),
            joinedload(models.EventSeries.group),
            joinedload(models.EventSeries.address),
        ]

    def get_series(self, series_id):
        return (
            self.db.query(models.EventSeries)
            .options(*self._series_options())
            .filter(models.EventSeries.id == series_id)
            .first()
        )

    def list_series(self, type_id=None, group_id=None, include_archived=False):
        query = self.db.query(models.EventSeries).options(*self._series_options())
        if type_id:
            query = query.filter(models.EventSeries.event_type_id == type_id)
        if group_id:
            query = query.filter(models.EventSeries.group_id == group_id)
        if not include_archived:
            query = query.filter(models.EventSeries.status == "active")
        return query.order_by(models.EventSeries.title.asc(), models.EventSeries.id.asc()).all()

    def series_in_window(self, start, end, type_ids=None, group_id=None, order_of_service_only=False):
        query = (
            self.db.query(models.EventSeries)
            .options(*self._series_options())
            .join(models.EventType)
            .filter(
                models.EventSeries.status == "active",
                models.EventSeries.start_date <= end,
                or_(models.EventSeries.until.is_(None), models.EventSeries.until >= start),
            )
        )
        return self._filter_series(query, type_ids, group_id, order_of_service_only).all()

    def occurrences_in_window(self, start, end, type_ids=None, group_id=None, order_of_service_only=False):
        query = (
            self.db.query(models.EventOccurrence)
            .options(
                joinedload(models.EventOccurrence.series).joinedload(models.EventSeries.event_type),
                joinedload(models.EventOccurrence.series).joinedload(models.EventSeries.group),
                joinedload(models.EventOccurrence.series).joinedload(models.EventSeries.address),
                joinedload(models.EventOccurrence.address),
            )
            .join(models.EventSeries, models.EventOccurrence.series_id == models.EventSeries.id)
            .join(models.EventType, models.EventSeries.event_type_id == models.EventType.id)
            .filter(
                models.EventSeries.status == "active",
                or_(
                    models.EventOccurrence.original_date.between(start, end),
                    models.EventOccurrence.moved_to_date.between(start, end),
                ),
            )
        )
        return self._filter_series(query, type_ids, group_id, order_of_service_only).all()

    def _filter_series(self, query, type_ids, group_id, order_of_service_only):
        if type_ids:
            query = query.filter(models.EventSeries.event_type_id.in_(type_ids))
        if group_id:
            query = query.filter(models.EventSeries.group_id == group_id)
        if order_of_service_only:
            query = query.filter(models.EventType.has_order_of_service.is_(True))
        return query

    def add_series(self, series):
        self.db.add(series)
        self.db.commit()
        return self.get_series(series.id)

    def save_series(self, series):
        series.updated_at = datetime.now()
        self.db.commit()
        return self.get_series(series.id)

    # Occurrences

    def get_occurrence(self, series_id, original_date):
        return (
            self.db.query(models.EventOccurrence)
            .options(joinedload(models.EventOccurrence.address))
            .filter(
                models.EventOccurrence.series_id == series_id,
                models.EventOccurrence.original_date == original_date,
            )
            .first()
        )

    def occurrences_for_series(self, series_id, from_date=None):
        query = self.db.query(models.EventOccurrence).filter(models.EventOccurrence.series_id == series_id)
        if from_date is not None:
            query = query.filter(models.EventOccurrence.original_date >= from_date)
        return query.order_by(models.EventOccurrence.original_date.asc()).all()

    def add_occurrence(self, occurrence):
        self.db.add(occurrence)
        self.db.commit()
        self.db.refresh(occurrence)
        return occurrence

    def save(self):
        self.db.commit()

    def flush(self):
        self.db.flush()

    def delete_occurrence(self, occurrence):
        self.db.delete(occurrence)

    def plan_counts(self, occurrence_ids):
        if not occurrence_ids:
            return {}
        rows = (
            self.db.query(models.ServicePlanItem.occurrence_id, func.count(models.ServicePlanItem.id))
            .filter(models.ServicePlanItem.occurrence_id.in_(occurrence_ids))
            .group_by(models.ServicePlanItem.occurrence_id)
            .all()
        )
        return {occurrence_id: count for occurrence_id, count in rows}

    def template_counts(self, series_ids):
        if not series_ids:
            return {}
        rows = (
            self.db.query(models.ServicePlanItem.series_id, func.count(models.ServicePlanItem.id))
            .filter(models.ServicePlanItem.series_id.in_(series_ids), models.ServicePlanItem.occurrence_id.is_(None))
            .group_by(models.ServicePlanItem.series_id)
            .all()
        )
        return {series_id: count for series_id, count in rows}

    # Order of service

    def template_items(self, series_id):
        return (
            self.db.query(models.ServicePlanItem)
            .options(joinedload(models.ServicePlanItem.song), joinedload(models.ServicePlanItem.person))
            .filter(models.ServicePlanItem.series_id == series_id, models.ServicePlanItem.occurrence_id.is_(None))
            .order_by(models.ServicePlanItem.position.asc(), models.ServicePlanItem.id.asc())
            .all()
        )

    def occurrence_items(self, occurrence_id):
        return (
            self.db.query(models.ServicePlanItem)
            .options(joinedload(models.ServicePlanItem.song), joinedload(models.ServicePlanItem.person))
            .filter(models.ServicePlanItem.occurrence_id == occurrence_id)
            .order_by(models.ServicePlanItem.position.asc(), models.ServicePlanItem.id.asc())
            .all()
        )

    def replace_template(self, series_id, items):
        self.db.query(models.ServicePlanItem).filter(
            models.ServicePlanItem.series_id == series_id, models.ServicePlanItem.occurrence_id.is_(None)
        ).delete(synchronize_session=False)
        for position, item in enumerate(items):
            item.series_id = series_id
            item.occurrence_id = None
            item.position = position
            self.db.add(item)

    def replace_occurrence_items(self, occurrence_id, items):
        self.db.query(models.ServicePlanItem).filter(
            models.ServicePlanItem.occurrence_id == occurrence_id
        ).delete(synchronize_session=False)
        for position, item in enumerate(items):
            item.series_id = None
            item.occurrence_id = occurrence_id
            item.position = position
            self.db.add(item)

    def song_exists(self, song_id):
        return self.db.query(Song.id).filter(Song.id == song_id).first() is not None

    # Church

    def church_address(self):
        church = (
            self.db.query(Church)
            .options(joinedload(Church.address))
            .order_by(Church.id.asc())
            .first()
        )
        return church.address if church else None

    # Song usage

    def song_usage_rows(self, start, end, song_id=None):
        effective = effective_date_column().label("effective_date")
        query = (
            self.db.query(
                models.ServicePlanItem.song_id,
                models.ServicePlanItem.song_key,
                effective,
                models.EventOccurrence.status,
                models.EventOccurrence.series_id,
                func.coalesce(models.EventOccurrence.title, models.EventSeries.title).label("title"),
            )
            .join(models.EventOccurrence, models.ServicePlanItem.occurrence_id == models.EventOccurrence.id)
            .join(models.EventSeries, models.EventOccurrence.series_id == models.EventSeries.id)
            .filter(models.ServicePlanItem.song_id.isnot(None))
        )
        if start is not None:
            query = query.filter(effective_date_column() >= start)
        if end is not None:
            query = query.filter(effective_date_column() <= end)
        if song_id is not None:
            query = query.filter(models.ServicePlanItem.song_id == song_id)
        return query.order_by(effective_date_column().desc()).all()

    def songs_by_ids(self, song_ids):
        if not song_ids:
            return {}
        return {song.id: song for song in self.db.query(Song).filter(Song.id.in_(song_ids)).all()}

    def last_used_by_song(self, song_ids, on_or_before):
        if not song_ids:
            return {}
        rows = (
            self.db.query(models.ServicePlanItem.song_id, func.max(effective_date_column()))
            .join(models.EventOccurrence, models.ServicePlanItem.occurrence_id == models.EventOccurrence.id)
            .filter(
                models.ServicePlanItem.song_id.in_(song_ids),
                models.EventOccurrence.status != "cancelled",
                effective_date_column() <= on_or_before,
            )
            .group_by(models.ServicePlanItem.song_id)
            .all()
        )
        return dict(rows)
