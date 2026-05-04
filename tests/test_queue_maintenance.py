from datetime import datetime, timedelta, timezone

from app import db
from app.models import Ticket


def test_flush_open_tickets_cli_closes_live_and_in_progress(test_app):
    """CLI flush should close active tickets and leave closed/resolved unchanged."""
    live = Ticket(
        student_name="Live", table="T1", physics_course="Ph 211", status="live"
    )
    in_progress = Ticket(
        student_name="InProgress",
        table="T2",
        physics_course="Ph 212",
        status="in_progress",
        number_of_students=3,
    )
    closed = Ticket(
        student_name="Closed",
        table="T3",
        physics_course="Ph 213",
        status="closed",
        closed_reason="helped",
        closed_at=datetime.now(timezone.utc) - timedelta(hours=1),
        number_of_students=2,
    )
    resolved = Ticket(
        student_name="Resolved",
        table="T4",
        physics_course="Ph 214",
        status="resolved",
        closed_reason="duplicate",
        closed_at=datetime.now(timezone.utc) - timedelta(hours=2),
        number_of_students=0,
    )

    db.session.add_all([live, in_progress, closed, resolved])
    db.session.commit()

    runner = test_app.test_cli_runner()
    result = runner.invoke(args=["flush-open-tickets", "--reason", "Queue Flushed"])

    assert result.exit_code == 0
    assert "2 ticket(s) closed" in result.output

    db.session.refresh(live)
    db.session.refresh(in_progress)
    db.session.refresh(closed)
    db.session.refresh(resolved)

    for ticket in (live, in_progress):
        assert ticket.status == "closed"
        assert ticket.closed_reason == "Queue Flushed"
        assert ticket.closed_at is not None
        assert ticket.number_of_students == 0

    assert closed.status == "closed"
    assert closed.closed_reason == "helped"
    assert resolved.status == "resolved"
    assert resolved.closed_reason == "duplicate"
