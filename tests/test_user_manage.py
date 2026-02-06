def test_user_add(test_client):
    response = test_client.post("/api/users_add_json", json={
        "username": "testusername",
        "email": "testemail123",
        "password": "testpass123",
        "is_admin": False
    }, follow_redirects=True)  # Add this!
    assert response.status_code == 201
    # Optional: check for flash message
    assert b'User added successfully!' in response.data

def test_user_remove(test_client):

    # create test user first
    response = test_client.post("/api/users_add_json", json={
        "username": "testusername",
        "email": "testemail123",
        "password": "testpass123",
        "is_admin": False
    })

    response = test_client.post("/api/users_remove", json={
        "username": "testusername"
    })
    data = response.get_json()
    assert data == {"success": "user removed"}

def test_user_add_admin(test_client):
    response = test_client.post("/api/users_add_json", json={
        "username": "testusername",
        "email": "testemail123",
        "password": "testpass123",
        "is_admin": True
    }, follow_redirects=True)  # Add this!
    assert response.status_code == 201

def test_user_add_no_email_no_pass_admin(test_client):
    response = test_client.post("/api/users_add_json", json={
        "username": "testusername",
        "email": "",
        "password": "",
        "is_admin": True
    }, follow_redirects=True)  # Add this!
    assert response.status_code == 201
    # This might actually fail validation and show error - you may need to adjust

def test_user_remove_no_email_no_pass_admin(test_client):
    response = test_client.post("/api/users_add_json", json={
        "username": "testusername",
        "email": "",
        "password": "",
        "is_admin": True
    })

    response = test_client.post("/api/users_remove", json={
        "username": "testusername"
    })
    data = response.get_json()
    assert data == {"success": "admin removed"}
