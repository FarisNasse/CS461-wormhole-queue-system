# tests/test_user_model.py

"""
User Model and Authentication Route Tests
=========================================

This module contains integration and unit tests for:
- User password hashing and validation
- Login/logout routes
- Session management and admin flag behavior
"""

from app.models import User
from app import db


# --------------------------------------------------------------------------
# User Model Tests
# --------------------------------------------------------------------------

def test_user_password_hashing(test_app):
    """Ensure password hashing and verification work correctly."""
    with test_app.app_context():
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")

        db.session.add(user)
        db.session.commit()

        saved_user = User.query.filter_by(username="testuser").first()

        assert saved_user is not None
        assert saved_user.check_password("password123")
        assert not saved_user.check_password("wrongpassword")


# --------------------------------------------------------------------------
# Login Route Tests
# --------------------------------------------------------------------------

def test_login_route_accepts_credentials(test_client, test_app):
    """Verify that valid credentials return a successful login response."""
    with test_app.app_context():
        u = User(username="tester", email="t@t.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()

    response = test_client.post("/api/login", json={
        "username": "tester",
        "password": "password123"
    })

    assert response.status_code == 200
    assert "Login successful" in response.get_data(as_text=True)


def test_login_route_rejects_invalid_credentials(test_client, test_app):
    """Ensure that login with invalid credentials returns an error."""
    with test_app.app_context():
        u = User(username="tester2", email="t2@t.com")
        u.set_password("password456")
        db.session.add(u)
        db.session.commit()

    response = test_client.post("/api/login", json={
        "username": "tester2",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Invalid credentials"


def test_login_nonexistent_user(test_client):
    """Ensure that login with a nonexistent user fails."""
    response = test_client.post("/api/login", json={
        "username": "ghostuser",
        "password": "whatever"
    })

    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Invalid credentials"


def test_login_missing_fields(test_client):
    """Ensure missing login fields return a 400 or 401 error."""
    response = test_client.post("/api/login", json={"username": "tester"})
    assert response.status_code in (400, 401)


def test_login_returns_admin_flag(test_client, test_app):
    """Verify that admin flag is correctly returned after login."""
    with test_app.app_context():
        u = User(username="adminuser", email="a@a.com", is_admin=True)
        u.set_password("adminpass")
        db.session.add(u)
        db.session.commit()

    response = test_client.post("/api/login", json={
        "username": "adminuser",
        "password": "adminpass"
    })

    data = response.get_json()
    assert response.status_code == 200
    assert data["is_admin"] is True


# --------------------------------------------------------------------------
# Session Management Tests
# --------------------------------------------------------------------------

def test_session_set_after_login(test_client, test_app):
    """Ensure user_id is added to session after successful login."""
    with test_app.app_context():
        u = User(username="sessionuser", email="s@s.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()

    with test_client as c:
        response = c.post("/api/login", json={
            "username": "sessionuser",
            "password": "password123"
        })

        assert response.status_code == 200
        with c.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["user_id"] is not None


def test_logout_clears_session(test_client, test_app):
    """Ensure logout clears the user session."""
    with test_app.app_context():
        u = User(username="logoutuser", email="l@l.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()

    with test_client as c:
        c.post("/api/login", json={"username": "logoutuser", "password": "password123"})
        with c.session_transaction() as sess:
            assert "user_id" in sess

        c.post("/api/logout")
        with c.session_transaction() as sess:
            assert "user_id" not in sess


# --------------------------------------------------------------------------
# Session Status Endpoint Tests
# --------------------------------------------------------------------------

def test_check_session_logged_in(test_client, test_app):
    """Verify that /api/check-session reports correct login status."""
    with test_app.app_context():
        u = User(username="checkuser", email="c@c.com", is_admin=True)
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()

    with test_client as c:
        c.post("/api/login", json={"username": "checkuser", "password": "password123"})
        response = c.get("/api/check-session")

        data = response.get_json()
        assert response.status_code == 200
        assert data["logged_in"] is True
        assert data["is_admin"] is True


def test_check_session_logged_out(test_client):
    """Verify that /api/check-session returns logged_in=False when logged out."""
    response = test_client.get("/api/check-session")
    data = response.get_json()

    assert response.status_code == 200
    assert data["logged_in"] is False
