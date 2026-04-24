"""Attendance helpers for check-ins, scheduled shifts, and activity tracking."""

from __future__ import annotations

from datetime import datetime, time, timezone
from types import SimpleNamespace

from sqlalchemy.orm import joinedload

from app import db
from app.time_utils import PACIFIC_TZ, format_pacific

ACTIVE_MINUTES = 5
IDLE_MINUTES = 15
SHIFT_GRACE_MINUTES = 15

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def ensure_aware_utc(value: datetime | None) -> datetime | None:
    """Normalize stored datetimes that may come back from SQLite as naive UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def active_attendance_session_for_user(user_id: int):
    """Return the user's open attendance session, if one exists."""
    from app.models import AttendanceSession

    return (
        AttendanceSession.query.filter(
            AttendanceSession.user_id == user_id,
            AttendanceSession.status == "active",
            AttendanceSession.checked_out_at.is_(None),
        )
        .order_by(AttendanceSession.checked_in_at.desc())
        .first()
    )


def _time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def shift_matches_moment(shift, moment: datetime | None = None) -> bool:
    """Return True when a shift is active around the current Pacific-local time."""
    moment = moment or utc_now()
    local_now = moment.astimezone(PACIFIC_TZ)
    if shift.day_of_week != local_now.weekday():
        return False

    current_minutes = _time_to_minutes(local_now.time())
    start_minutes = _time_to_minutes(shift.start_time) - SHIFT_GRACE_MINUTES
    end_minutes = _time_to_minutes(shift.end_time) + SHIFT_GRACE_MINUTES
    return start_minutes <= current_minutes <= end_minutes


def current_shift_for_user(user_id: int, moment: datetime | None = None):
    """Find the active scheduled shift for a user, allowing a small grace period."""
    from app.models import AttendanceShift

    moment = moment or utc_now()
    local_now = moment.astimezone(PACIFIC_TZ)
    shifts = (
        AttendanceShift.query.filter_by(
            user_id=user_id,
            day_of_week=local_now.weekday(),
            is_active=True,
        )
        .order_by(AttendanceShift.start_time)
        .all()
    )
    for shift in shifts:
        if shift_matches_moment(shift, moment):
            return shift
    return None


def attendance_status_for_session(session, moment: datetime | None = None) -> str:
    """Return a derived present/idle/stale/checked-out status label."""
    if session is None:
        return "Missing"
    if session.checked_out_at is not None or session.status == "checked_out":
        return "Checked out"

    current_moment = moment if moment is not None else utc_now()
    current_moment = (
        current_moment.astimezone(timezone.utc)
        if current_moment.tzinfo
        else current_moment.replace(tzinfo=timezone.utc)
    )

    last_seen = ensure_aware_utc(session.last_seen_at)
    if last_seen is None:
        last_seen = ensure_aware_utc(session.checked_in_at)
    if last_seen is None:
        return "Stale"

    elapsed_minutes = (current_moment - last_seen).total_seconds() / 60

    if elapsed_minutes <= ACTIVE_MINUTES:
        return "Present"
    if elapsed_minutes <= IDLE_MINUTES:
        return "Idle"
    return "Stale"


def attendance_status_slug(status: str) -> str:
    """Normalize a status label for CSS class names."""
    return status.lower().replace(" ", "-")


def touch_attendance(user_id: int, commit: bool = True):
    """Refresh the last-seen timestamp for a user's active attendance session."""
    active_session = active_attendance_session_for_user(user_id)
    if active_session:
        active_session.last_seen_at = utc_now()
        if commit:
            db.session.commit()
    return active_session


def record_attendance_activity(
    user_id: int,
    activity_type: str,
    description: str,
    ticket_id: int | None = None,
    commit: bool = True,
):
    """Create an attendance activity row and update last_seen for active sessions."""
    from app.models import AttendanceActivity

    active_session = active_attendance_session_for_user(user_id)
    now = utc_now()

    if active_session:
        active_session.last_seen_at = now

    activity = AttendanceActivity(
        user_id=user_id,
        attendance_session_id=active_session.id if active_session else None,
        ticket_id=ticket_id,
        activity_type=activity_type,
        description=description,
        created_at=now,
    )
    db.session.add(activity)

    if commit:
        db.session.commit()

    return activity


def format_shift_time_range(shift) -> str:
    """Return a compact local time range for a scheduled shift."""
    return (
        f"{DAY_NAMES[shift.day_of_week]} "
        f"{shift.start_time.strftime('%I:%M %p').lstrip('0')}–"
        f"{shift.end_time.strftime('%I:%M %p').lstrip('0')}"
    )


def build_attendance_dashboard(moment: datetime | None = None):
    """Build dashboard rows comparing scheduled shifts against live check-ins."""
    from app.models import AttendanceSession, AttendanceShift

    moment = moment or utc_now()
    local_now = moment.astimezone(PACIFIC_TZ)

    active_sessions = (
        AttendanceSession.query.options(
            joinedload(AttendanceSession.user),
            joinedload(AttendanceSession.shift),
        )
        .filter(
            AttendanceSession.status == "active",
            AttendanceSession.checked_out_at.is_(None),
        )
        .order_by(AttendanceSession.checked_in_at)
        .all()
    )
    sessions_by_user_id = {session.user_id: session for session in active_sessions}

    todays_shifts = (
        AttendanceShift.query.options(joinedload(AttendanceShift.user))
        .filter_by(
            day_of_week=local_now.weekday(),
            is_active=True,
        )
        .order_by(AttendanceShift.start_time)
        .all()
    )
    scheduled_now = [
        shift for shift in todays_shifts if shift_matches_moment(shift, moment)
    ]

    rows = []
    scheduled_user_ids = set()

    for shift in scheduled_now:
        scheduled_user_ids.add(shift.user_id)
        session = sessions_by_user_id.get(shift.user_id)
        status = (
            attendance_status_for_session(session, moment) if session else "Missing"
        )
        rows.append(
            SimpleNamespace(
                user=shift.user,
                schedule=format_shift_time_range(shift),
                location=shift.location,
                checked_in_at=session.checked_in_at if session else None,
                last_seen_at=session.last_seen_at if session else None,
                status=status,
                status_slug=attendance_status_slug(status),
                session=session,
                source="scheduled",
            )
        )

    for session in active_sessions:
        if session.user_id in scheduled_user_ids:
            continue
        status = attendance_status_for_session(session, moment)
        rows.append(
            SimpleNamespace(
                user=session.user,
                schedule="Unscheduled check-in",
                location=session.shift.location if session.shift else "Wormhole",
                checked_in_at=session.checked_in_at,
                last_seen_at=session.last_seen_at,
                status=status,
                status_slug=attendance_status_slug(status),
                session=session,
                source="unscheduled",
            )
        )

    summary = SimpleNamespace(
        present=sum(1 for row in rows if row.status == "Present"),
        idle=sum(1 for row in rows if row.status == "Idle"),
        stale=sum(1 for row in rows if row.status == "Stale"),
        missing=sum(1 for row in rows if row.status == "Missing"),
        total=len(rows),
    )

    return rows, summary


def format_datetime_for_display(value: datetime | None, fmt: str = "%I:%M %p") -> str:
    """Format a UTC datetime in Pacific time for templates or JSON responses."""
    if value is None:
        return "—"
    return format_pacific(ensure_aware_utc(value), fmt)
