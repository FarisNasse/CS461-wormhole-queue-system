from datetime import datetime, time, timedelta, timezone

from app import db
from app.attendance_utils import (
    PACIFIC_TZ,
    attendance_status_for_session,
)
from app.models import AttendanceActivity, AttendanceSession, AttendanceShift, Ticket, User


def _login_as(test_client, user):
    with test_client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["is_admin"] = user.is_admin


def _create_user(username, *, is_admin=False, name=None):
    user = User(
        username=username,
        email=f"{username}@test.com",
        name=name,
        is_admin=is_admin,
    )
    user.set_password("pass")
    db.session.add(user)
    db.session.commit()
    return user


def _full_day_shift_for_user(user):
    now_pacific = datetime.now(timezone.utc).astimezone(PACIFIC_TZ)
    shift = AttendanceShift(
        user_id=user.id,
        day_of_week=now_pacific.weekday(),
        start_time=time(0, 0),
        end_time=time(23, 59),
        location="Wormhole",
        is_active=True,
    )
    db.session.add(shift)
    db.session.commit()
    return shift


def test_attendance_check_in_heartbeat_and_check_out(test_client, test_app):
    """Assistants can check in, send heartbeat, and check out with activity logged."""
    with test_app.app_context():
        user = _create_user("attendant")
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


def test_duplicate_check_in_does_not_create_duplicate_active_sessions(
    test_client, test_app
):
    """Double-clicking check-in should not create multiple open sessions."""
    with test_app.app_context():
        user = _create_user("duplicate_helper")
        _login_as(test_client, user)

        first_response = test_client.post("/attendance/check-in", follow_redirects=True)
        second_response = test_client.post("/attendance/check-in", follow_redirects=True)

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert b"You are already checked in to the Wormhole." in second_response.data
        assert AttendanceSession.query.filter_by(
            user_id=user.id,
            status="active",
        ).count() == 1
        assert AttendanceActivity.query.filter_by(
            user_id=user.id,
            activity_type="check_in",
        ).count() == 1


def test_heartbeat_without_active_session_is_safe(test_client, test_app):
    """Heartbeat should be harmless when a logged-in user is not checked in."""
    with test_app.app_context():
        user = _create_user("heartbeat_only")
        _login_as(test_client, user)

        response = test_client.post("/attendance/heartbeat")

        assert response.status_code == 200
        assert response.get_json() == {"ok": True, "checked_in": False}
        assert AttendanceSession.query.filter_by(user_id=user.id).count() == 0


def test_attendance_requires_login(test_client):
    """Unauthenticated users should not be able to check in or heartbeat."""
    check_in_response = test_client.post("/attendance/check-in")
    heartbeat_response = test_client.post("/attendance/heartbeat")

    assert check_in_response.status_code == 401
    assert heartbeat_response.status_code == 401


def test_admin_can_create_attendance_shift(test_client, test_app):
    """Admins can create recurring scheduled attendance shifts."""
    with test_app.app_context():
        admin = _create_user("shift_admin", is_admin=True)
        assistant = _create_user("scheduled_assistant", name="Scheduled Assistant")
        _login_as(test_client, admin)

        response = test_client.post(
            "/attendance/shifts/add",
            data={
                "user_id": str(assistant.id),
                "day_of_week": "0",
                "start_time": "09:00",
                "end_time": "17:00",
                "location": "Wormhole Desk",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Attendance shift added." in response.data

        shift = AttendanceShift.query.filter_by(user_id=assistant.id).one()
        assert shift.day_of_week == 0
        assert shift.start_time == time(9, 0)
        assert shift.end_time == time(17, 0)
        assert shift.location == "Wormhole Desk"
        assert shift.is_active is True


def test_non_admin_cannot_create_attendance_shift(test_client, test_app):
    """Regular assistants cannot manage the recurring attendance schedule."""
    with test_app.app_context():
        user = _create_user("regular_helper")
        other_assistant = _create_user("other_helper")
        _login_as(test_client, user)

        response = test_client.post(
            "/attendance/shifts/add",
            data={
                "user_id": str(other_assistant.id),
                "day_of_week": "0",
                "start_time": "09:00",
                "end_time": "17:00",
                "location": "Wormhole",
            },
        )

        assert response.status_code == 403
        assert AttendanceShift.query.filter_by(user_id=other_assistant.id).count() == 0


def test_invalid_shift_times_are_rejected(test_client, test_app):
    """The app should reject shifts whose end time is not after the start time."""
    with test_app.app_context():
        admin = _create_user("invalid_shift_admin", is_admin=True)
        assistant = _create_user("invalid_shift_helper")
        _login_as(test_client, admin)

        response = test_client.post(
            "/attendance/shifts/add",
            data={
                "user_id": str(assistant.id),
                "day_of_week": "0",
                "start_time": "17:00",
                "end_time": "09:00",
                "location": "Wormhole",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Shift end time must be after the start time." in response.data
        assert AttendanceShift.query.filter_by(user_id=assistant.id).count() == 0


def test_admin_can_soft_delete_attendance_shift(test_client, test_app):
    """Deleting a shift should deactivate it instead of destroying history."""
    with test_app.app_context():
        admin = _create_user("delete_shift_admin", is_admin=True)
        assistant = _create_user("delete_shift_helper")
        shift = _full_day_shift_for_user(assistant)
        shift_id = shift.id
        _login_as(test_client, admin)

        response = test_client.post(
            f"/attendance/shifts/{shift_id}/delete",
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Attendance shift removed." in response.data
        deactivated_shift = db.session.get(AttendanceShift, shift_id)
        assert deactivated_shift is not None
        assert deactivated_shift.is_active is False


def test_attendance_dashboard_shows_scheduled_missing_assistant(test_client, test_app):
    """Admins can see scheduled assistants who have not checked in."""
    with test_app.app_context():
        admin = _create_user("attendance_admin", is_admin=True)
        assistant = _create_user(
            "scheduled_helper",
            name="Scheduled Helper",
        )
        _full_day_shift_for_user(assistant)
        _login_as(test_client, admin)

        response = test_client.get("/attendance/")
        assert response.status_code == 200
        assert b"Scheduled Helper" in response.data
        assert b"Missing" in response.data


def test_check_in_attaches_to_current_scheduled_shift(test_client, test_app):
    """A check-in during a matching scheduled shift should link to that shift."""
    with test_app.app_context():
        assistant = _create_user("matched_shift_helper")
        shift = _full_day_shift_for_user(assistant)
        _login_as(test_client, assistant)

        response = test_client.post("/attendance/check-in", follow_redirects=True)

        assert response.status_code == 200
        attendance_session = AttendanceSession.query.filter_by(
            user_id=assistant.id,
            status="active",
        ).one()
        assert attendance_session.shift_id == shift.id
        assert attendance_session.notes is None


def test_unscheduled_check_in_is_allowed_and_visible_to_admin(test_client, test_app):
    """Coverage helpers should appear even when they check in outside a shift."""
    with test_app.app_context():
        admin = _create_user("unscheduled_admin", is_admin=True)
        assistant = _create_user("unscheduled_helper", name="Unscheduled Helper")
        _login_as(test_client, assistant)

        check_in_response = test_client.post("/attendance/check-in", follow_redirects=True)
        assert check_in_response.status_code == 200

        attendance_session = AttendanceSession.query.filter_by(
            user_id=assistant.id,
            status="active",
        ).one()
        assert attendance_session.shift_id is None
        assert attendance_session.notes == "Checked in outside a scheduled shift."

        _login_as(test_client, admin)
        dashboard_response = test_client.get("/attendance/")
        assert dashboard_response.status_code == 200
        assert b"Unscheduled Helper" in dashboard_response.data
        assert b"Unscheduled check-in" in dashboard_response.data
        assert b"Present" in dashboard_response.data


def test_attendance_status_distinguishes_present_idle_and_stale(test_app):
    """Last-seen timestamps should drive present, idle, and stale status labels."""
    with test_app.app_context():
        user = _create_user("status_helper")
        now = datetime.now(timezone.utc)
        attendance_session = AttendanceSession(
            user_id=user.id,
            checked_in_at=now - timedelta(minutes=30),
            last_seen_at=now,
            status="active",
        )
        db.session.add(attendance_session)
        db.session.commit()

        assert attendance_status_for_session(attendance_session, now) == "Present"

        attendance_session.last_seen_at = now - timedelta(minutes=10)
        assert attendance_status_for_session(attendance_session, now) == "Idle"

        attendance_session.last_seen_at = now - timedelta(minutes=20)
        assert attendance_status_for_session(attendance_session, now) == "Stale"

        attendance_session.status = "checked_out"
        attendance_session.checked_out_at = now
        assert attendance_status_for_session(attendance_session, now) == "Checked out"


def test_queue_page_shows_attendance_summary_for_admin(test_client, test_app):
    """The existing queue dashboard should include a compact attendance snapshot."""
    with test_app.app_context():
        admin = _create_user("queue_admin", is_admin=True)
        assistant = _create_user("queue_missing_helper", name="Queue Missing Helper")
        _full_day_shift_for_user(assistant)
        _login_as(test_client, admin)

        response = test_client.get("/queue")

        assert response.status_code == 200
        assert b"Attendance Snapshot" in response.data
        assert b"Queue Missing Helper" in response.data
        assert b"Missing" in response.data


def test_ticket_claim_creates_attendance_activity(test_client, test_app):
    """Claiming a ticket records queue activity for the checked-in assistant."""
    with test_app.app_context():
        user = _create_user("claim_helper")
        ticket = Ticket(
            student_name="Queue Student",
            table="Zoom",
            physics_course="Ph 211",
            status="live",
        )
        db.session.add(ticket)
        db.session.commit()
        _login_as(test_client, user)

        test_client.post("/attendance/check-in", follow_redirects=True)
        response = test_client.get(f"/getnewticket/{user.username}", follow_redirects=False)
        assert response.status_code == 302

        activity = AttendanceActivity.query.filter_by(
            user_id=user.id, activity_type="ticket_claimed"
        ).one()
        assert activity.ticket_id == ticket.id
        assert activity.attendance_session_id is not None
        assert "Claimed ticket" in activity.description


def test_ticket_resolution_creates_attendance_activity(test_client, test_app):
    """Resolving a ticket should be included in the assistant activity log."""
    with test_app.app_context():
        user = _create_user("resolve_helper")
        ticket = Ticket(
            student_name="Resolved Student",
            table="3",
            physics_course="Ph 212",
            status="in_progress",
            wa_id=user.id,
        )
        db.session.add(ticket)
        db.session.commit()
        _login_as(test_client, user)

        test_client.post("/attendance/check-in", follow_redirects=True)
        response = test_client.post(
            f"/api/resolveticket/{ticket.id}",
            data={"resolve": "helped", "numstudents": "1"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        activity = AttendanceActivity.query.filter_by(
            user_id=user.id,
            ticket_id=ticket.id,
            activity_type="ticket_resolved",
        ).one()
        assert "Resolved ticket" in activity.description
