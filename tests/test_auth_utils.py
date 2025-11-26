#tests/test_auth_utils.py

import pytest
from flask import Flask, jsonify
from app.auth_utils import login_required, admin_required

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def auth_test_client():
    """
    Creates a dedicated temporary Flask app with routes pre-registered.
    This avoids the "dynamic route registration" issue flagged by the reviewer.
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.secret_key = "test_secret"

    # Register routes ONCE here, instead of inside every test function
    
    @app.route("/protected-login")
    @login_required
    def protected_login():
        return jsonify({"message": "ok"})

    @app.route("/protected-admin")
    @admin_required
    def protected_admin():
        return jsonify({"message": "ok"})

    return app.test_client()


# --------------------------------------------------------------------------
# Login Required Tests
# --------------------------------------------------------------------------

def test_login_required_blocks_unauthenticated(auth_test_client):
    """Ensure users without a session are rejected."""
    res = auth_test_client.get("/protected-login")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Authentication required"


def test_login_required_allows_authenticated(auth_test_client):
    """[NEW] Ensure users with a valid session are allowed."""
    # Create a valid user session
    with auth_test_client.session_transaction() as sess:
        sess["user_id"] = 123
    
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
    # Create a non-admin session
    with auth_test_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["is_admin"] = False

    res = auth_test_client.get("/protected-admin")
    assert res.status_code == 403
    assert res.get_json()["error"] == "Admin access required"


def test_admin_required_allows_admin(auth_test_client):
    """Ensure admin users are allowed."""
    # Create an admin session
    with auth_test_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["is_admin"] = True

    res = auth_test_client.get("/protected-admin")
    assert res.status_code == 200
    assert res.get_json()["message"] == "ok"

