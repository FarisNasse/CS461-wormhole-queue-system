import pytest
from app import db, mail
from app.models import User, Ticket
from app.email_utils import send_unclosed_ticket_reminders 

def test_consolidated_ta_reminder(test_app):
    """Verify one TA with multiple tickets gets one consolidated email."""
    with test_app.app_context():
        ta = User(username="physics_ta", email="ta@example.edu", is_admin=False)
        db.session.add(ta)
        db.session.commit()

        t1 = Ticket(student_name="Alice", status="current", wa_id=ta.id, physics_course="PH201", table="1")
        t2 = Ticket(student_name="Bob", status="current", wa_id=ta.id, physics_course="PH202", table="2")
        db.session.add_all([t1, t2])
        db.session.commit()

        with mail.record_messages() as outbox:
            send_unclosed_ticket_reminders()
            assert len(outbox) == 1
            # FIX 1: Change .to to .recipients
            assert outbox[0].recipients == ["ta@example.edu"]
            assert "Alice" in outbox[0].body
            assert "Bob" in outbox[0].body

def test_admin_alert_for_live_tickets(test_app):
    """Verify admins get notified about unassigned live tickets."""
    with test_app.app_context():
        admin = User(username="boss", email="admin@example.edu", is_admin=True)
        db.session.add(admin)
        
        t = Ticket(student_name="Charlie", status="live", wa_id=None, physics_course="PH211", table="A")
        db.session.add(t)
        db.session.commit()

        with mail.record_messages() as outbox:
            send_unclosed_ticket_reminders()
            # FIX 2: Change .to to .recipients
            assert any(admin.email in msg.recipients for msg in outbox)

def test_no_reminders_for_closed_tickets(test_app):
    """Verify no emails are sent if all tickets are closed."""
    with test_app.app_context():
        # FIX 3: Add 'table' and 'physics_course' to satisfy database constraints
        t = Ticket(student_name="Dave", status="closed", closed_reason="helped", table="B", physics_course="PH203")
        db.session.add(t)
        db.session.commit()

        with mail.record_messages() as outbox:
            send_unclosed_ticket_reminders()
            assert len(outbox) == 0