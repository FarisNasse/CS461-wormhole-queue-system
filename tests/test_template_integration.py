from app.models import User, db


def test_userpage_renders_user(test_client, test_app):
    with test_app.app_context():
        u = User(username="sam", email="s@osu.edu")
        u.set_password("pw")
        db.session.add(u)
        db.session.commit()

    test_client.post("/api/login", json={"username": "sam", "password": "pw"})
    resp = test_client.get("/profile")

    assert resp.status_code == 200
    assert b"sam" in resp.data


def test_admin_utilities_only_visible_for_admin(test_client, test_app):
    with test_app.app_context():
        admin = User(username="admin", email="a@osu.edu", is_admin=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

    test_client.post("/api/login", json={"username": "admin", "password": "pw"})
    resp = test_client.get("/profile")

    assert resp.status_code == 200
    assert b"Admin" in resp.data
