# tests/test_user_model.py
"""
User Model and Authentication Integration Tests
Updated for Flask-Login
"""
from app.models import User
from app import db
from flask_login import current_user

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

def test_login_logs_user_in(test_client, test_app):
    """Ensure valid credentials log the user in via Flask-Login."""
    with test_app.app_context():
        u = User(username="tester", email="t@t.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()

    # Attempt Login
    response = test_client.post("/api/login", json={
        "username": "tester",
        "password": "password123"
    })

    assert response.status_code == 200
    assert "Login successful" in response.get_data(as_text=True)

    # Verify login by accessing a protected route (Dashboard)
    # If logged in, we get 200. If not, we get 302 (Redirect) or 401.
    resp = test_client.get("/dashboard")
    assert resp.status_code == 200

def test_login_rejects_invalid_credentials(test_client, test_app):
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

def test_logout_clears_session(test_client, test_app):
    """Ensure logout actually logs the user out."""
    # 1. Create User
    with test_app.app_context():
        u = User(username="logoutuser", email="l@l.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

    # 2. Login
    test_client.post("/api/login", json={"username": "logoutuser", "password": "pass"})
    
    # Verify we are logged in
    assert test_client.get("/dashboard").status_code == 200

    # 3. Logout
    test_client.get("/api/logout")

    # 4. Verify we are logged out (Dashboard redirects to login)
    resp = test_client.get("/dashboard")
    assert resp.status_code == 302  # Redirects to /assistant-login