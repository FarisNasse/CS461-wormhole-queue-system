def test_user_add(test_client):
    response = test_client.post("/users_add", json={
        "username": "testusername",
        "email": "testemail123",
        "password": "testpass123",
        "is_admin": False
    })
    assert reponse.status_code == 201

def test_user_remove(test_client):
    response = test_client.post("/users_add", json={
        "username": "testusername"
    })
    assert response.status_code == 200