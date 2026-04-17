from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Treat naive datetimes from the DB as UTC and return an aware datetime."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_pacific(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert a datetime to America/Los_Angeles for display."""
    aware_utc = ensure_aware_utc(dt)
    if aware_utc is None:
        return None
    return aware_utc.astimezone(PACIFIC_TZ)


def format_pacific(dt: Optional[datetime], fmt: str = "%b %d %I:%M:%S %p %Z") -> str:
    """Format a datetime in Pacific Time for user-facing displays."""
    pacific_dt = to_pacific(dt)
    if pacific_dt is None:
        return "N/A"
    return pacific_dt.strftime(fmt)


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime as an explicit UTC ISO 8601 string."""
    aware_utc = ensure_aware_utc(dt)
    if aware_utc is None:
        return None
    return aware_utc.isoformat()


def pacific_day_bounds_to_utc(day: date) -> Tuple[datetime, datetime]:
    """Return the UTC datetimes spanning a full Pacific local date."""
    start_local = datetime.combine(day, time.min, tzinfo=PACIFIC_TZ)
    end_local = datetime.combine(day, time.max, tzinfo=PACIFIC_TZ)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)
