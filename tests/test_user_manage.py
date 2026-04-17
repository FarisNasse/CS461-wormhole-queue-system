import io

from app import db
from app.models import User


def test_user_add(test_client):
    response = test_client.post(
        "/api/users_add_json",
        json={
            "username": "testusername",
            "email": "testemail123",
            "password": "testpass123",
            "is_admin": False,
        },
        follow_redirects=True,
    )
    assert response.status_code == 201


def test_user_created_active_by_default(test_client, test_app):
    """New users should have their `is_active` flag set to True automatically."""
    username = "activeuser"
    # create user via API
    resp = test_client.post(
        "/api/users_add_json",
        json={
            "username": username,
            "email": "active@user.com",
            "password": "pw",
            "is_admin": False,
        },
    )
    assert resp.status_code == 201

    with test_app.app_context():
        from app.models import User

        u = User.query.filter_by(username=username).first()
        assert u is not None
        assert u.is_active is True


def test_user_remove(test_client):
    # create test user first
    response = test_client.post(
        "/api/users_add_json",
        json={
            "username": "testusername",
            "email": "testemail123",
            "password": "testpass123",
            "is_admin": False,
        },
    )

    response = test_client.post("/api/users_remove", json={"username": "testusername"})
    data = response.get_json()
    assert data == {"success": "user removed"}


def test_user_add_admin(test_client):
    response = test_client.post(
        "/api/users_add_json",
        json={
            "username": "testusername",
            "email": "testemail123",
            "password": "testpass123",
            "is_admin": True,
        },
        follow_redirects=True,
    )
    assert response.status_code == 201


def test_user_add_no_email_no_pass_admin(test_client):
    response = test_client.post(
        "/api/users_add_json",
        json={
            "username": "testusername",
            "email": "",
            "password": "",
            "is_admin": True,
        },
        follow_redirects=True,
    )
    assert response.status_code == 201


def test_user_remove_no_email_no_pass_admin(test_client):
    response = test_client.post(
        "/api/users_add_json",
        json={
            "username": "testusername",
            "email": "",
            "password": "",
            "is_admin": True,
        },
    )

    response = test_client.post("/api/users_remove", json={"username": "testusername"})
    data = response.get_json()
    assert data == {"success": "admin removed"}


def test_users_add_batch_csv_creates_non_admin_users(test_client, test_app):
    csv_content = "first name,last name,ONID\n" "Jane,Doe,jdoe\n" "John,Smith,jsmith\n"

    with test_app.app_context():
        admin = User(
            username="admin_batch", email="admin_batch@test.com", is_admin=True
        )
        admin.set_password("pass")
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id

    with test_client.session_transaction() as sess:
        sess["user_id"] = admin_id
        sess["is_admin"] = True

    response = test_client.post(
        "/api/users_add_batch",
        data={"user_csv": (io.BytesIO(csv_content.encode("utf-8")), "users.csv")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with test_app.app_context():
        jane = User.query.filter_by(username="jdoe").first()
        john = User.query.filter_by(username="jsmith").first()

        assert jane is not None
        assert john is not None
        assert jane.name == "Jane Doe"
        assert john.name == "John Smith"
        assert jane.email == "jdoe@oregonstate.edu"
        assert john.email == "jsmith@oregonstate.edu"
        assert jane.is_admin is False
        assert john.is_admin is False


def test_users_add_batch_blocks_non_admin(test_client, test_app):
    csv_content = "first name,last name,ONID\n" "Sam,Lee,slee\n"

    with test_app.app_context():
        user = User(
            username="regular_batch", email="regular_batch@test.com", is_admin=False
        )
        user.set_password("pass")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["is_admin"] = False

    response = test_client.post(
        "/api/users_add_batch",
        data={"user_csv": (io.BytesIO(csv_content.encode("utf-8")), "users.csv")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 403
    assert response.get_json() == {"error": "Admin access required"}

    with test_app.app_context():
        created = User.query.filter_by(username="slee").first()
        assert created is None
