# tests/test_admin_security.py
from app import db
from app.models import User


def test_non_admin_cannot_access_register(test_client, test_app):
    """Ensure a standard user gets a 403 Forbidden when visiting /register."""
    # 1. Create Standard User
    with test_app.app_context():
        u = User(username="std_user", email="std@test.com", is_admin=False)
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

    # 2. Login
    test_client.post("/api/login", json={"username": "std_user", "password": "pass"})

    # 3. Attempt to access Admin Route
    resp = test_client.get("/register")

    # Should be 403 (Forbidden)
    assert resp.status_code == 403


def test_admin_can_access_register(test_client, test_app):
    """Ensure an Admin user gets a 200 OK when visiting /register."""
    # 1. Create Admin
    with test_app.app_context():
        admin = User(username="the_boss", email="boss@test.com", is_admin=True)
        admin.set_password("pass")
        db.session.add(admin)
        db.session.commit()

    # 2. Login
    test_client.post("/api/login", json={"username": "the_boss", "password": "pass"})

    # 3. Attempt to access Admin Route
    resp = test_client.get("/register")

    # Should be 200 (Success)
    assert resp.status_code == 200
    assert b"New User Registration" in resp.data
