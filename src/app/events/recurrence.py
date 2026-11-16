"""Expand an event schedule into dates.

Supported patterns: once-off, weekly on chosen days, every N weeks, monthly on
the nth weekday (several positions allowed, such as the 1st and 3rd Monday, or
-1 for the last), monthly on the start date's day, and yearly.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from dateutil import rrule

WEEKDAYS = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
FREQUENCIES = ("weekly", "monthly", "yearly")
POSITIONS = (1, 2, 3, 4, 5, -1)

_RRULE_FREQ = {"weekly": rrule.WEEKLY, "monthly": rrule.MONTHLY, "yearly": rrule.YEARLY}
_RRULE_DAY = dict(zip(WEEKDAYS, (rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU)))
_DAY_NAMES = dict(zip(WEEKDAYS, ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")))
_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", -1: "last"}


class InvalidRecurrence(ValueError):
    pass


@dataclass(frozen=True)
class Schedule:
    start_date: datetime.date
    frequency: str | None = None
    interval: int = 1
    weekdays: tuple[str, ...] = field(default_factory=tuple)
    positions: tuple[int, ...] = field(default_factory=tuple)
    until: datetime.date | None = None

    @property
    def is_recurring(self) -> bool:
        return self.frequency is not None


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def schedule_from_series(series) -> Schedule:
    return Schedule(
        start_date=series.start_date,
        frequency=series.frequency,
        interval=series.interval or 1,
        weekdays=tuple(parse_list(series.by_weekday)),
        positions=tuple(int(value) for value in parse_list(series.by_set_pos)),
        until=series.until,
    )


def validate(schedule: Schedule) -> Schedule:
    """Return a normalised schedule or raise InvalidRecurrence."""
    if schedule.frequency is None:
        return Schedule(start_date=schedule.start_date)
    if schedule.frequency not in FREQUENCIES:
        raise InvalidRecurrence(f"Frequency must be one of {', '.join(FREQUENCIES)}")
    if not 1 <= schedule.interval <= 52:
        raise InvalidRecurrence("Interval must be between 1 and 52")
    if schedule.until is not None and schedule.until < schedule.start_date:
        raise InvalidRecurrence("The end date must be on or after the start date")
    unknown = [day for day in schedule.weekdays if day not in WEEKDAYS]
    if unknown:
        raise InvalidRecurrence(f"Unknown weekday: {', '.join(unknown)}")
    bad_positions = [value for value in schedule.positions if value not in POSITIONS]
    if bad_positions:
        raise InvalidRecurrence("Positions must be 1 to 5, or -1 for the last")
    weekdays = tuple(day for day in WEEKDAYS if day in schedule.weekdays)
    positions = tuple(sorted(set(schedule.positions), key=lambda value: (value < 0, value)))
    if schedule.frequency == "weekly":
        weekdays = weekdays or (WEEKDAYS[schedule.start_date.weekday()],)
        positions = ()
    elif schedule.frequency == "monthly":
        if positions and not weekdays:
            raise InvalidRecurrence("Choose a weekday for a monthly nth-weekday pattern")
        if weekdays and not positions:
            raise InvalidRecurrence("Choose which week of the month (1st, 2nd, last...)")
    else:
        weekdays = ()
        positions = ()
    return Schedule(
        start_date=schedule.start_date,
        frequency=schedule.frequency,
        interval=schedule.interval,
        weekdays=weekdays,
        positions=positions,
        until=schedule.until,
    )


def _rule(schedule: Schedule) -> rrule.rrule:
    kwargs = {
        "dtstart": datetime.datetime.combine(schedule.start_date, datetime.time()),
        "interval": schedule.interval,
    }
    if schedule.until is not None:
        kwargs["until"] = datetime.datetime.combine(schedule.until, datetime.time())
    if schedule.frequency == "weekly":
        kwargs["byweekday"] = [_RRULE_DAY[day] for day in schedule.weekdays]
    elif schedule.frequency == "monthly" and schedule.weekdays:
        kwargs["byweekday"] = [
            _RRULE_DAY[day](position) for day in schedule.weekdays for position in schedule.positions
        ]
    return rrule.rrule(_RRULE_FREQ[schedule.frequency], **kwargs)


def dates_between(schedule: Schedule, start: datetime.date, end: datetime.date) -> list[datetime.date]:
    """Every scheduled date from start to end inclusive."""
    if end < start:
        return []
    if not schedule.is_recurring:
        return [schedule.start_date] if start <= schedule.start_date <= end else []
    window_start = max(start, schedule.start_date)
    window_end = min(end, schedule.until) if schedule.until else end
    if window_end < window_start:
        return []
    rule = _rule(schedule)
    found = rule.between(
        datetime.datetime.combine(window_start, datetime.time()),
        datetime.datetime.combine(window_end, datetime.time()),
        inc=True,
    )
    return [value.date() for value in found]


def occurs_on(schedule: Schedule, day: datetime.date) -> bool:
    return day in dates_between(schedule, day, day)


def next_date(schedule: Schedule, after: datetime.date) -> datetime.date | None:
    if not schedule.is_recurring:
        return schedule.start_date if schedule.start_date >= after else None
    start = max(after, schedule.start_date)
    if schedule.until and start > schedule.until:
        return None
    found = _rule(schedule).after(datetime.datetime.combine(start, datetime.time()), inc=True)
    return found.date() if found else None


def _join(words: list[str]) -> str:
    if len(words) <= 1:
        return "".join(words)
    return f"{', '.join(words[:-1])} and {words[-1]}"


def describe(schedule: Schedule) -> str:
    """A short human label, for example '1st and 3rd Monday of every month'."""
    if not schedule.is_recurring:
        return "Once-off"
    days = _join([_DAY_NAMES[day] for day in schedule.weekdays])
    every = schedule.interval
    if schedule.frequency == "weekly":
        label = f"Weekly on {days}" if every == 1 else f"Every {every} weeks on {days}"
    elif schedule.frequency == "monthly":
        unit = "every month" if every == 1 else f"every {every} months"
        if schedule.weekdays:
            positions = _join([_ORDINALS[value] for value in schedule.positions])
            label = f"{positions} {days} of {unit}"
        else:
            day = schedule.start_date.day
            suffix = "th" if 11 <= day % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            label = f"Monthly on the {day}{suffix}" if every == 1 else f"On the {day}{suffix} {unit}"
        label = label[0].upper() + label[1:]
    else:
        when = schedule.start_date.strftime("%-d %B")
        label = f"Yearly on {when}" if every == 1 else f"Every {every} years on {when}"
    if schedule.until:
        label += f", until {schedule.until.strftime('%-d %b %Y')}"
    return label
