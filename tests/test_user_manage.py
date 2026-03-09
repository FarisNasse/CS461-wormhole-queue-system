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
    )  # Add this!
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
    )  # Add this!
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
    )  # Add this!
    assert response.status_code == 201
    # This might actually fail validation and show error - you may need to adjust


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
