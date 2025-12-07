from datetime import UTC, datetime, timedelta

from app import db
from app.models import Ticket, User


def test_ticket_defaults(test_app):
    """
    Unit Test: Ensure created_at and status defaults are applied correctly.
    """
    with test_app.app_context():
        t = Ticket(student_name="Time Traveler", table="A1", physics_course="PH 101")
        db.session.add(t)
        db.session.commit()

        # Check Defaults
        assert t.status == "Open"
        assert t.created_at is not None

        # FIX: Ensure DB timestamp is treated as UTC for comparison
        db_time = t.created_at
        if db_time.tzinfo is None:
            db_time = db_time.replace(tzinfo=UTC)

        # Verify it's a recent time (approx now)
        # Now both sides of the subtraction are offset-aware
        assert (datetime.now(UTC) - db_time) < timedelta(seconds=5)


def test_ticket_wa_assignment(test_app):
    """
    Relationship Test: Ensure a ticket can be linked to a User (WA).
    """
    with test_app.app_context():
        # Create User (WA)
        wa = User(username="helper", email="help@osu.edu")
        wa.set_password("pass")
        db.session.add(wa)
        db.session.commit()

        # Create Ticket linked to WA
        t = Ticket(
            student_name="Help Me",
            table="B3",
            physics_course="PH 201",
            wa_id=wa.id,
            status="Assigned",
        )
        db.session.add(t)
        db.session.commit()

        # Verify Link
        fetched_ticket = Ticket.query.filter_by(student_name="Help Me").first()
        assert fetched_ticket.wa_id == wa.id
