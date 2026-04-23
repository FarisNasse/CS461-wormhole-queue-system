from datetime import datetime, time, timezone

from app import db
from app.attendance_utils import PACIFIC_TZ
from app.models import AttendanceActivity, AttendanceSession, AttendanceShift, Ticket, User


def _login_as(test_client, user):
    with test_client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["is_admin"] = user.is_admin


def test_attendance_check_in_heartbeat_and_check_out(test_client, test_app):
    """Assistants can check in, send heartbeat, and check out with activity logged."""
    with test_app.app_context():
        user = User(username="attendant", email="attendant@test.com", is_admin=False)
        user.set_password("pass")
        db.session.add(user)
        db.session.commit()
        _login_as(test_client, user)

        response = test_client.post("/attendance/check-in", follow_redirects=True)
        assert response.status_code == 200
        assert b"You are now checked in to the Wormhole." in response.data

        attendance_session = AttendanceSession.query.filter_by(user_id=user.id).one()
        assert attendance_session.status == "active"
        assert attendance_session.checked_out_at is None
        assert AttendanceActivity.query.filter_by(
            user_id=user.id, activity_type="check_in"
        ).count() == 1

        first_seen = attendance_session.last_seen_at
        heartbeat_response = test_client.post("/attendance/heartbeat")
        assert heartbeat_response.status_code == 200
        assert heartbeat_response.get_json()["checked_in"] is True

        db.session.refresh(attendance_session)
        assert attendance_session.last_seen_at >= first_seen

        response = test_client.post("/attendance/check-out", follow_redirects=True)
        assert response.status_code == 200
        assert b"You have checked out of the Wormhole." in response.data

        db.session.refresh(attendance_session)
        assert attendance_session.status == "checked_out"
        assert attendance_session.checked_out_at is not None
        assert AttendanceActivity.query.filter_by(
            user_id=user.id, activity_type="check_out"
        ).count() == 1


def test_attendance_dashboard_shows_scheduled_missing_assistant(test_client, test_app):
    """Admins can see scheduled assistants who have not checked in."""
    with test_app.app_context():
        admin = User(username="attendance_admin", email="aa@test.com", is_admin=True)
        assistant = User(
            username="scheduled_helper",
            email="scheduled@test.com",
            name="Scheduled Helper",
            is_admin=False,
        )
        admin.set_password("pass")
        assistant.set_password("pass")
        db.session.add_all([admin, assistant])
        db.session.commit()

        now_pacific = datetime.now(timezone.utc).astimezone(PACIFIC_TZ)
        shift = AttendanceShift(
            user_id=assistant.id,
            day_of_week=now_pacific.weekday(),
            start_time=time(0, 0),
            end_time=time(23, 59),
            location="Wormhole",
            is_active=True,
        )
        db.session.add(shift)
        db.session.commit()

        _login_as(test_client, admin)

        response = test_client.get("/attendance/")
        assert response.status_code == 200
        assert b"Scheduled Helper" in response.data
        assert b"Missing" in response.data


def test_ticket_claim_creates_attendance_activity(test_client, test_app):
    """Claiming a ticket records queue activity for the checked-in assistant."""
    with test_app.app_context():
        user = User(username="claim_helper", email="claim@test.com", is_admin=False)
        user.set_password("pass")
        ticket = Ticket(
            student_name="Queue Student",
            table="Zoom",
            physics_course="Ph 211",
            status="live",
        )
        db.session.add_all([user, ticket])
        db.session.commit()
        _login_as(test_client, user)

        test_client.post("/attendance/check-in", follow_redirects=True)
        response = test_client.get(f"/getnewticket/{user.username}", follow_redirects=False)
        assert response.status_code == 302

        activity = AttendanceActivity.query.filter_by(
            user_id=user.id, activity_type="ticket_claimed"
        ).one()
        assert activity.ticket_id == ticket.id
        assert "Claimed ticket" in activity.description
