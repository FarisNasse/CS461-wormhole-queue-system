# tests/test_routes.py
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def test_assistant_login_inactive_user(test_client, test_app):
    """Ensure that form-based login rejects inactive users."""
    with test_app.app_context():
        u = User(username="inactiveform", email="if@i.com", is_active=False)
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

    response = test_client.post(
        "/assistant-login",
        data={"username": "inactiveform", "password": "pass"},
        follow_redirects=True,
    )
    # should not redirect to hardware_list; instead show error message
    assert b"This account has been deactivated." in response.data


def test_dashboard_is_protected(test_client):
    """Verify that '/dashboard' blocks users who are NOT logged in."""
    response = test_client.get("/dashboard")
    assert response.status_code == 401


def test_dashboard_access_granted(test_client, test_app):
    """
    Verify that '/dashboard' allows users who ARE logged in.
    We simulate a login by manually setting the session cookie.
    """
    with test_app.app_context():
        u = User(username="testuser", email="test@example.com")
        u.set_password("password")
        db.session.add(u)
        db.session.commit()
        user_id = u.id

    # 1. Simulate a logged-in user by setting the session
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id  # Use real user ID
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
        closed_at_aware = (
            ticket.closed_at.replace(tzinfo=timezone.utc)
            if ticket.closed_at.tzinfo is None
            else ticket.closed_at
        )
        assert now - closed_at_aware < timedelta(minutes=1)


def test_clear_queue_route_resets_ticket_index(test_client):
    """Clear queue should permanently remove tickets and restart IDs at 1."""
    admin = User(username="admin_clear", email="clear@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)

    t1 = Ticket(student_name="S1", table="T1", physics_course="Ph 211", status="live")
    t2 = Ticket(student_name="S2", table="T2", physics_course="Ph 212", status="closed")
    db.session.add_all([t1, t2])
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    response = test_client.post("/clear_queue", follow_redirects=True)
    assert response.status_code == 200
    assert b"Queue data cleared permanently" in response.data

    assert Ticket.query.count() == 0

    new_ticket = Ticket(
        student_name="AfterClear",
        table="T9",
        physics_course="Ph 213",
        status="live",
    )
    db.session.add(new_ticket)
    db.session.commit()
    assert new_ticket.id == 1


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

    response = test_client.post("/archive/export", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert b"Archive created: wormhole_archive_" in response.data
    assert b"Create Archive" in response.data


def test_archive_page_lists_saved_files(test_client, test_app):
    """Archive page should show links for saved CSV files."""
    admin = User(username="admin_list", email="list@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)
    db.session.commit()

    archive_dir = Path(test_app.root_path) / "data" / "archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    filename = "wormhole_archive_test_listing.csv"
    file_path = archive_dir / filename
    file_path.write_text("id,name\n1,Test\n", encoding="utf-8")

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    response = None
    try:
        response = test_client.get("/archive")
        assert response.status_code == 200
        assert filename.encode("utf-8") in response.data
    finally:
        if response is not None:
            response.close()
        if file_path.exists():
            file_path.unlink()


def test_download_archive_serves_csv_file(test_client, test_app):
    """Archive download route should return saved CSV file contents."""
    admin = User(username="admin_download", email="download@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)
    db.session.commit()

    archive_dir = Path(test_app.root_path) / "data" / "archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    filename = "wormhole_archive_test_download.csv"
    file_path = archive_dir / filename
    file_path.write_text("Ticket ID,Student Name\n1,DownloadMe\n", encoding="utf-8")

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    response = None
    try:
        response = test_client.get(f"/archive/download/{filename}")
        assert response.status_code == 200
        assert b"DownloadMe" in response.data
        assert "attachment;" in response.headers.get("Content-Disposition", "")
    finally:
        if response is not None:
            response.close()
        if file_path.exists():
            file_path.unlink()


def test_delete_archives_removes_selected_file(test_client, test_app):
    """Archive delete route should remove selected CSV file(s)."""
    admin = User(username="admin_delete", email="delete@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)
    db.session.commit()

    archive_dir = Path(test_app.root_path) / "data" / "archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    filename = "wormhole_archive_test_delete.csv"
    file_path = archive_dir / filename
    file_path.write_text("Ticket ID,Student Name\n1,DeleteMe\n", encoding="utf-8")

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    response = test_client.post(
        "/archive/delete",
        data={"filenames": [filename]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Deleted 1 archive file(s)." in response.data
    assert not file_path.exists()


def test_delete_archives_with_no_selection(test_client, test_app):
    """Archive delete route should inform admin when nothing is selected."""
    admin = User(username="admin_delete_none", email="deletenone@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    response = test_client.post("/archive/delete", data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b"No archive files selected." in response.data


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


def test_flash_message_category_rendering(test_client):
    """Verify that flash messages are rendered with the correct CSS class."""
    # 1. Create a dummy admin user in the database (or use an existing one)

    admin = User(username="admin_test", email="admin_test@test.com", is_admin=True)
    admin.set_password("pass")
    db.session.add(admin)
    db.session.commit()

    # 2. Log in as the admin in the session
    with test_client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["is_admin"] = True

    # 3. Now trigger the 'success' flash via user registration
    data = {
        "first_name": "Test",
        "last_name": "User",
        "onid": "testflash",
        "is_admin": False,
    }

    # Submit the request
    response = test_client.post("/api/users_add", data=data, follow_redirects=True)

    # 4. Assertions
    assert response.status_code == 200
    assert b'class="flash-success"' in response.data
    assert b"User created successfully!" in response.data


def test_livequeuetickets_includes_in_progress_in_order(test_client):
    """Public live queue API should include both live and in-progress tickets in queue order."""
    t1 = Ticket(
        student_name="First", table="T1", physics_course="Ph 211", status="live"
    )
    t2 = Ticket(
        student_name="Second",
        table="T2",
        physics_course="Ph 212",
        status="in_progress",
    )
    t3 = Ticket(
        student_name="Third", table="T3", physics_course="Ph 213", status="live"
    )
    db.session.add_all([t1, t2, t3])
    db.session.commit()

    response = test_client.get("/api/livequeuetickets")

    assert response.status_code == 200
    payload = response.get_json()
    assert [ticket["student_name"] for ticket in payload] == [
        "First",
        "Second",
        "Third",
    ]
    assert [ticket["status"] for ticket in payload] == ["live", "in_progress", "live"]
