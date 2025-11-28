import json
from app.models import User, db

def create_user(username, password, is_admin=False):
    user = User(username=username, email=f"{username}@osu.edu", is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

def login_helper(client, username, password):
    return client.post(
        "/api/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json"
    )


def test_successful_login(test_client, test_app):
    with test_app.app_context():
        create_user("faris", "secret")

    resp = login_helper(test_client, "faris", "secret")
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Login successful"


def test_logout_clears_session(test_client, test_app):
    with test_app.app_context():
        create_user("faris", "secret")

    login_helper(test_client, "faris", "secret")
    test_client.post("/api/logout")

    resp = test_client.get("/dashboard")
    assert resp.status_code == 302
    assert "/assistant-login" in resp.headers.get("Location", "")


def test_admin_can_access_profile(test_client, test_app):
    with test_app.app_context():
        create_user("admin", "pw", is_admin=True)

    login_helper(test_client, "admin", "pw")
    resp = test_client.get("/profile")
    assert resp.status_code == 200


def test_user_can_access_profile(test_client, test_app):
    with test_app.app_context():
        create_user("u", "pw")

    login_helper(test_client, "u", "pw")
    resp = test_client.get("/profile")
    assert resp.status_code == 200
