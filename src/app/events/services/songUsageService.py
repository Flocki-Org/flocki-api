import csv
import datetime
import io

from fastapi import Depends

from src.app.events.daos.eventDAO import EventDAO
from src.app.events.models.events import SongHistoryEntry, SongUsageDetail, SongUsageView


class SongUsageService:
    """Song usage comes from saved orders of service on dates that were not cancelled."""

    def __init__(self, dao: EventDAO = Depends(EventDAO)):
        self.dao = dao

    def usage(self, start: datetime.date, end: datetime.date, limit: int | None = None):
        rows = [row for row in self.dao.song_usage_rows(start, end) if row.status != "cancelled"]
        counts = {}
        last_used = {}
        for row in rows:
            counts[row.song_id] = counts.get(row.song_id, 0) + 1
            if row.song_id not in last_used or row.effective_date > last_used[row.song_id]:
                last_used[row.song_id] = row.effective_date
        songs = self.dao.songs_by_ids(list(counts))
        views = [
            SongUsageView(
                song_id=song_id,
                name=songs[song_id].name if song_id in songs else None,
                code=songs[song_id].code if song_id in songs else None,
                ccli_number=songs[song_id].ccli_number if song_id in songs else None,
                times_used=count,
                last_used=last_used.get(song_id),
            )
            for song_id, count in counts.items()
        ]
        views.sort(key=lambda view: (-view.times_used, (view.name or "").lower()))
        return views[:limit] if limit else views

    def detail(self, song_id: int, today: datetime.date | None = None):
        today = today or datetime.date.today()
        rows = self.dao.song_usage_rows(None, None, song_id=song_id)
        year_ago = today - datetime.timedelta(days=365)
        played = [row for row in rows if row.status != "cancelled" and row.effective_date <= today]
        upcoming = [row for row in rows if row.status != "cancelled" and row.effective_date > today]
        return SongUsageDetail(
            song_id=song_id,
            times_used_last_12_months=sum(1 for row in played if row.effective_date >= year_ago),
            last_used=max((row.effective_date for row in played), default=None),
            next_scheduled=min((row.effective_date for row in upcoming), default=None),
            history=[
                SongHistoryEntry(
                    date=row.effective_date,
                    series_id=row.series_id,
                    title=row.title,
                    song_key=row.song_key,
                    cancelled=row.status == "cancelled",
                )
                for row in rows[:50]
            ],
        )

    def last_used(self, song_ids, today: datetime.date | None = None):
        return self.dao.last_used_by_song(song_ids, today or datetime.date.today())

    def ccli_csv(self, start: datetime.date, end: datetime.date) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Song", "CCLI number", "Times used", "Last used"])
        for view in self.usage(start, end):
            writer.writerow([view.name or "", view.ccli_number or "", view.times_used,
                             view.last_used.isoformat() if view.last_used else ""])
        return buffer.getvalue()
