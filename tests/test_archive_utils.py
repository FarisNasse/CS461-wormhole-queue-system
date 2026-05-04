import csv
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from app import db
from app.models import Ticket, User


def test_archive_weekly_cli_appends_previous_week_once(test_app):
    """Weekly archive command appends the completed Sat-to-Sat week only once."""
    pacific = ZoneInfo("America/Los_Angeles")
    assistant = User(
        username="weeklyhelper",
        email="weeklyhelper@test.com",
        name="=Weekly Helper",
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

    archive_filename = f"wormhole_archive_weekly_cli_{uuid4().hex}.csv"
    archive_path = Path(test_app.root_path) / "data" / "archives" / archive_filename

    runner = test_app.test_cli_runner()
    try:
        first_run = runner.invoke(
            args=[
                "archive-weekly",
                "--now",
                "2026-04-25T00:00:00-07:00",
                "--filename",
                archive_filename,
            ]
        )
        assert first_run.exit_code == 0
        assert "1 row(s) appended" in first_run.output
        assert archive_path.exists()

        with archive_path.open("r", encoding="utf-8", newline="") as archive_file:
            rows = list(csv.DictReader(archive_file))

        assert len(rows) == 1
        assert rows[0]["Student Name"] == "Inside Week"
        assert rows[0]["Status"] == "closed"
        assert rows[0]["Created At"] == "2026-04-20 10:00:00"
        assert rows[0]["Closed At"] == "2026-04-20 12:00:00"
        assert rows[0]["Assistant Name"] == "'=Weekly Helper"

        second_run = runner.invoke(
            args=[
                "archive-weekly",
                "--now",
                "2026-04-25T00:00:00-07:00",
                "--filename",
                archive_filename,
            ]
        )
        assert second_run.exit_code == 0
        assert "0 row(s) appended" in second_run.output
        assert "1 duplicate row(s) skipped" in second_run.output

        with archive_path.open("r", encoding="utf-8", newline="") as archive_file:
            rows = list(csv.DictReader(archive_file))

        assert len(rows) == 1
    finally:
        if archive_path.exists():
            archive_path.unlink()


def test_archive_weekly_cli_confines_filename_to_archive_directory(test_app):
    """CLI-provided archive names cannot escape the archive directory."""
    pacific = ZoneInfo("America/Los_Angeles")
    ticket = Ticket(
        student_name="Safe Filename",
        table="T1",
        physics_course="PH 211",
        status="closed",
        closed_reason="helped",
        number_of_students=1,
    )
    ticket.created_at = datetime(2026, 4, 20, 10, 0, tzinfo=pacific).astimezone(
        timezone.utc
    )
    ticket.closed_at = datetime(2026, 4, 20, 12, 0, tzinfo=pacific).astimezone(
        timezone.utc
    )
    db.session.add(ticket)
    db.session.commit()

    archive_dir = Path(test_app.root_path) / "data" / "archives"
    archive_path = archive_dir / "unsafe_name.csv"
    escaped_path = archive_dir.parent / "unsafe_name.csv"

    runner = test_app.test_cli_runner()
    try:
        result = runner.invoke(
            args=[
                "archive-weekly",
                "--now",
                "2026-04-25T00:00:00-07:00",
                "--filename",
                "../unsafe_name",
            ]
        )

        assert result.exit_code == 0
        assert archive_path.exists()
        assert not escaped_path.exists()
    finally:
        if archive_path.exists():
            archive_path.unlink()
        if escaped_path.exists():
            escaped_path.unlink()
