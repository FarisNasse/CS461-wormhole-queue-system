# tests/test_auth_utils.py

from flask import jsonify
from app.auth_utils import login_required, admin_required


def test_login_required_blocks_unauthenticated(test_client):
    app = test_client.application

    @app.route("/protected-login")
    @login_required
    def protected_login():
        return jsonify({"message": "ok"})

    res = test_client.get("/protected-login")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Authentication required"


def test_admin_required_blocks_unauthenticated(test_client):
    app = test_client.application

    @app.route("/protected-admin")
    @admin_required
    def protected_admin():
        return jsonify({"message": "ok"})

    res = test_client.get("/protected-admin")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Authentication required"


def test_admin_required_blocks_non_admin(test_client):
    app = test_client.application

    @app.route("/protected-admin2")
    @admin_required
    def protected_admin2():
        return jsonify({"message": "ok"})

    # Create a fake non-admin session
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["is_admin"] = False

    res = test_client.get("/protected-admin2")
    assert res.status_code == 403
    assert res.get_json()["error"] == "Admin access required"


def test_admin_required_allows_admin(test_client):
    app = test_client.application

    @app.route("/protected-admin3")
    @admin_required
    def protected_admin3():
        return jsonify({"message": "ok"})

    # Create an admin session
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["is_admin"] = True

    res = test_client.get("/protected-admin3")
    assert res.status_code == 200
    assert res.get_json()["message"] == "ok"
