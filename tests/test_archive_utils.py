import csv
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from app import db
from app.archive_utils import CUMULATIVE_ARCHIVE_FILENAME
from app.models import Ticket, User


def test_archive_weekly_cli_appends_previous_week_once(test_app):
    """Weekly archive command appends the completed Sat-to-Sat week only once."""
    pacific = ZoneInfo("America/Los_Angeles")
    assistant = User(
        username="weeklyhelper",
        email="weeklyhelper@test.com",
        name="Weekly Helper",
    )
    assistant.set_password("pass")
    db.session.add(assistant)
    db.session.commit()

    inside_week = Ticket(
        student_name="Inside Week",
        table="T1",
        physics_course="PH 211",
        status="closed",
        closed_reason="helped",
        wa_id=assistant.id,
        number_of_students=2,
    )
    inside_week.created_at = datetime(2026, 4, 20, 10, 0, tzinfo=pacific).astimezone(
        timezone.utc
    )
    inside_week.closed_at = datetime(2026, 4, 20, 12, 0, tzinfo=pacific).astimezone(
        timezone.utc
    )

    before_week = Ticket(
        student_name="Before Week",
        table="T2",
        physics_course="PH 212",
        status="closed",
        closed_reason="helped",
    )
    before_week.created_at = datetime(2026, 4, 17, 20, 0, tzinfo=pacific).astimezone(
        timezone.utc
    )
    before_week.closed_at = datetime(2026, 4, 17, 23, 59, tzinfo=pacific).astimezone(
        timezone.utc
    )

    next_week_boundary = Ticket(
        student_name="Next Week Boundary",
        table="T3",
        physics_course="PH 213",
        status="closed",
        closed_reason="helped",
    )
    next_week_boundary.created_at = datetime(
        2026, 4, 24, 23, 0, tzinfo=pacific
    ).astimezone(timezone.utc)
    next_week_boundary.closed_at = datetime(
        2026, 4, 25, 0, 0, tzinfo=pacific
    ).astimezone(timezone.utc)

    db.session.add_all([inside_week, before_week, next_week_boundary])
    db.session.commit()

    archive_path = Path(test_app.root_path) / "data" / "archives" / CUMULATIVE_ARCHIVE_FILENAME
    if archive_path.exists():
        archive_path.unlink()

    runner = test_app.test_cli_runner()
    first_run = runner.invoke(
        args=["archive-weekly", "--now", "2026-04-25T00:00:00-07:00"]
    )
    assert first_run.exit_code == 0
    assert "1 row(s) appended" in first_run.output
    assert archive_path.exists()

    with archive_path.open("r", encoding="utf-8", newline="") as archive_file:
        rows = list(csv.DictReader(archive_file))

    assert len(rows) == 1
    assert rows[0]["Student Name"] == "Inside Week"
    assert rows[0]["Assistant Name"] == "Weekly Helper"

    second_run = runner.invoke(
        args=["archive-weekly", "--now", "2026-04-25T00:00:00-07:00"]
    )
    assert second_run.exit_code == 0
    assert "0 row(s) appended" in second_run.output
    assert "1 duplicate row(s) skipped" in second_run.output

    with archive_path.open("r", encoding="utf-8", newline="") as archive_file:
        rows = list(csv.DictReader(archive_file))

    assert len(rows) == 1

    archive_path.unlink()
