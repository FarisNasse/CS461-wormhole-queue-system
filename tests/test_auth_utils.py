# tests/test_auth_utils.py

import pytest
from flask import jsonify

from app.auth_utils import admin_required, login_required

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture
def auth_test_client():
    """
    Creates a dedicated temporary Flask app with routes pre-registered.
    This avoids the "dynamic route registration" issue flagged by the reviewer.
    """
    from app import create_app, db

    app = create_app(testing=True)
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()

        # Register routes ONCE here, instead of inside every test function

        @app.route("/protected-login")
        @login_required
        def protected_login():
            return jsonify({"message": "ok"})

        @app.route("/protected-admin")
        @admin_required
        def protected_admin():
            return jsonify({"message": "ok"})

        yield app.test_client()

        db.session.remove()
        db.drop_all()


# --------------------------------------------------------------------------
# Login Required Tests
# --------------------------------------------------------------------------


def test_login_required_blocks_unauthenticated(auth_test_client):
    """Ensure users without a session are rejected."""
    res = auth_test_client.get("/protected-login")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Authentication required"


def test_login_required_allows_authenticated(auth_test_client):
    """Ensure users with a valid session are allowed."""
    from app import db
    from app.models import User

    # Create a valid user
    with auth_test_client.application.app_context():
        u = User(username="testuser", email="test@example.com")
        db.session.add(u)
        db.session.commit()
        user_id = u.id

    # Create a valid user session
    with auth_test_client.session_transaction() as sess:
        sess["user_id"] = user_id

    res = auth_test_client.get("/protected-login")
    assert res.status_code == 200
    assert res.get_json()["message"] == "ok"


# --------------------------------------------------------------------------
# Admin Required Tests
# --------------------------------------------------------------------------


def test_admin_required_blocks_unauthenticated(auth_test_client):
    """Ensure users without a session are rejected from admin routes."""
    res = auth_test_client.get("/protected-admin")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Authentication required"


def test_admin_required_blocks_non_admin(auth_test_client):
    """Ensure logged-in users who are NOT admins are rejected."""
    from app import db
    from app.models import User

    # Create a non-admin user
    with auth_test_client.application.app_context():
        u = User(username="nonadmin", email="na@example.com", is_admin=False)
        db.session.add(u)
        db.session.commit()
        user_id = u.id

    # Create a non-admin session
    with auth_test_client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["is_admin"] = False

    res = auth_test_client.get("/protected-admin")
    assert res.status_code == 403
    assert res.get_json()["error"] == "Admin access required"


def test_admin_required_allows_admin(auth_test_client):
    """Ensure admin users are allowed."""
    from app import db
    from app.models import User

    # Create an admin user
    with auth_test_client.application.app_context():
        u = User(username="admin", email="admin@example.com", is_admin=True)
        db.session.add(u)
        db.session.commit()
        user_id = u.id

    # Create an admin session
    with auth_test_client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["is_admin"] = True

    res = auth_test_client.get("/protected-admin")
    assert res.status_code == 200
    assert res.get_json()["message"] == "ok"
