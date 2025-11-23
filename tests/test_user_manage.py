def test_user_add(test_client):
    response = test_client.post("/api/users_add", json={
        "username": "testusername",
        "email": "testemail123",
        "password": "testpass123",
        "is_admin": False
    })
    assert response.status_code == 201

def test_user_remove(test_client):

    # create test user first
    response = test_client.post("/api/users_add", json={
        "username": "testusername",
        "email": "testemail123",
        "password": "testpass123",
        "is_admin": False
    })

    response = test_client.post("/api/users_remove", json={
        "username": "testusername"
    })
    assert response.status_code == 200
