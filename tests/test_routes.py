# tests/test_routes.py
from datetime import datetime, timedelta, timezone

from app import db
from app.models import Ticket, User


def test_health_check_route(test_client):
    """Test the /health route returns 200 and the correct JSON message."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Wormhole Queue System API is running"}


def test_404_for_unknown_route(test_client):
    """Test that a non-existent route returns a 404 error."""
    response = test_client.get("/non_existent_route")
    assert response.status_code == 404


def test_home_page_loads(test_client):
    """Verify the root route '/' loads the Student Home Page (index.html)."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Physics Collaboration and Help Center" in response.data


def test_login_route_exists(test_client):
    """Verify the login route is accessible."""
    response = test_client.get("/assistant-login")
    assert response.status_code == 200
    assert b"Sign In" in response.data


def test_assistant_login_page_loads(test_client):
    """Verify '/assistant-login' loads the Login Page (login.html)."""
    response = test_client.get("/assistant-login")
    assert response.status_code == 200
    assert b"Assistant Login" in response.data


def test_dashboard_is_protected(test_client):
    """Verify that '/dashboard' blocks users who are NOT logged in."""
    response = test_client.get("/dashboard")
    assert response.status_code == 401


def test_dashboard_access_granted(test_client):
    """Verify that '/dashboard' allows users who ARE logged in."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["is_admin"] = False
    response = test_client.get("/dashboard")
    assert response.status_code == 200


def test_flush_route(test_client):
    """Test that flushing the queue closes all live tickets (Admin Only)."""
    admin = User(username="admin_flush", email="flush@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)

    t1 = Ticket(student_name="S1", table="T1", physics_course="Ph 211", status="live")
    t2 = Ticket(student_name="S2", table="T2", physics_course="Ph 212", status="live")
    t3 = Ticket(
        student_name="S3", table="T3", physics_course="Ph 213", status="in_progress"
    )
    db.session.add_all([t1, t2, t3])
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    response = test_client.post("/flush", follow_redirects=True)
    assert response.status_code == 200
    assert b"Queue flushed" in response.data  # Matches partial string check

    # Refresh objects from DB to see the update from the separate request context
    db.session.refresh(t1)
    db.session.refresh(t2)
    db.session.refresh(t3)
    assert t1.status == "closed"
    assert t1.closed_reason == "Queue Flushed"
    assert t2.status == "closed"
    assert t2.closed_reason == "Queue Flushed"
    assert t3.status == "closed"
    assert t3.closed_reason == "Queue Flushed"

    # Verify that closed_at has been set recently for all flushed tickets
    now = datetime.now(timezone.utc)
    for ticket in (t1, t2, t3):
        assert ticket.closed_at is not None
        assert isinstance(ticket.closed_at, datetime)
        # Ensure ticket.closed_at is timezone-aware before comparison
        closed_at_aware = ticket.closed_at.replace(tzinfo=timezone.utc) if ticket.closed_at.tzinfo is None else ticket.closed_at
        assert now - closed_at_aware < timedelta(minutes=1)


def test_export_archive(test_client):
    """Test archive export generates CSV with correct content."""
    admin = User(username="admin_arch", email="arch@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)

    # Use relative date (Yesterday) to avoid hardcoded dates becoming stale
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    t = Ticket(
        student_name="ExportMe", table="T1", physics_course="Ph 211", status="closed"
    )
    t.closed_at = yesterday
    db.session.add(t)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    data = {
        "start_date": yesterday.strftime("%Y-%m-%d"),
        "end_date": yesterday.strftime("%Y-%m-%d"),
    }

    response = test_client.post("/archive/export", data=data)
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert b"ExportMe" in response.data


def test_pastticket_resolution(test_client):
    """Test resolving a past ticket via POST (Happy Path)."""
    user = User(username="helper", email="help@test.com", is_admin=False)
    user.set_password("pass")
    db.session.add(user)

    t = Ticket(student_name="Old", table="T1", physics_course="Ph 211", status="live")
    db.session.add(t)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["is_admin"] = False

    data = {"resolveReason": "helped", "numStds": 2}
    response = test_client.post(
        f"/pastticket/helper/{t.id}", data=data, follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Ticket resolved successfully" in response.data

    db.session.refresh(t)
    assert t.status == "closed"
    assert t.closed_reason == "helped"
    assert t.number_of_students == 2


def test_pastticket_forbidden_for_other_user(test_client):
    """Regular users should not resolve past tickets under another user's URL."""
    owner = User(username="owner", email="owner@test.com", is_admin=False)
    other = User(username="other", email="other@test.com", is_admin=False)
    owner.set_password("pass")
    other.set_password("pass")
    db.session.add_all([owner, other])

    t = Ticket(
        student_name="Student", table="T2", physics_course="Ph 212", status="live"
    )
    db.session.add(t)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = owner.id
        sess["is_admin"] = False

    response = test_client.post(
        f"/pastticket/other/{t.id}", data={"resolveReason": "helped"}
    )
    assert response.status_code == 403


def test_pastticket_admin_can_access_any_user(test_client):
    """Admins should be able to resolve past tickets for any user's URL."""
    admin = User(username="admin_past", email="admin@test.com", is_admin=True)
    other = User(username="other_u", email="other@test.com", is_admin=False)
    admin.set_password("pass")
    other.set_password("pass")
    db.session.add_all([admin, other])

    t = Ticket(student_name="Old", table="T3", physics_course="Ph 213", status="live")
    db.session.add(t)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    # Use a valid choice defined in ResolveTicketForm
    data = {"resolveReason": "helped", "numStds": 1}

    response = test_client.post(
        f"/pastticket/other_u/{t.id}", data=data, follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(t)
    assert t.status == "closed"
    assert t.closed_reason == "helped"
