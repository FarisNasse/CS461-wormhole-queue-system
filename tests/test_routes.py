# tests/test_routes.py
from datetime import datetime, timezone

from app import db
from app.models import Ticket, User


def test_health_check_route(test_client):
    """Test the /health route returns 200 and the correct JSON message."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Wormhole Queue System API is running"}


def test_home_page_loads(test_client):
    """Verify the root route '/' loads the Student Home Page (index.html)."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Physics Collaboration and Help Center" in response.data


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
    # Create an admin user
    admin = User(username="admin_flush", email="flush@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)

    # Create live tickets
    t1 = Ticket(student_name="S1", table="T1", physics_course="Ph 211", status="live")
    t2 = Ticket(student_name="S2", table="T2", physics_course="Ph 212", status="live")
    db.session.add_all([t1, t2])
    db.session.commit()

    # Login as admin
    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    response = test_client.get("/flush", follow_redirects=True)
    assert response.status_code == 200
    assert b"Queue flushed" in response.data

    # Verify DB state
    assert t1.status == "closed"
    assert t1.closed_reason == "Queue Flushed"
    assert t2.status == "closed"


def test_export_archive(test_client):
    """Test archive export generates CSV with correct content."""
    admin = User(username="admin_arch", email="arch@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)

    # Use a fixed date to avoid timezone shifts during the test
    test_date = datetime(2026, 2, 16, 12, 0, 0, tzinfo=timezone.utc)

    t = Ticket(
        student_name="ExportMe", table="T1", physics_course="Ph 211", status="closed"
    )
    t.closed_at = test_date  # Fixed UTC time
    db.session.add(t)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    # Send the date string that matches the fixed test_date
    data = {
        "start_date": "2026-02-16",
        "end_date": "2026-02-16",
        "csrf_token": "",  # Ensure CSRF is handled if enabled
    }

    response = test_client.post("/archive/export", data=data)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"
    assert b"ExportMe" in response.data


def test_pastticket_resolution(test_client):
    """Test resolving a past ticket via POST."""
    user = User(username="helper", email="help@test.com", is_admin=False)
    user.set_password("pass")
    db.session.add(user)

    t = Ticket(student_name="Old", table="T1", physics_course="Ph 211", status="live")
    db.session.add(t)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = user.id

    data = {"resolveReason": "helped", "numStds": 2}
    response = test_client.post(
        f"/pastticket/helper/{t.id}", data=data, follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Ticket resolved successfully" in response.data
    assert t.status == "closed"
    assert t.closed_reason == "helped"
    assert t.number_of_students == 2
