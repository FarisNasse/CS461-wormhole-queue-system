# tests/test_routes.py
def test_health_check_route(test_client):
    """Test the /health route returns 200 and the correct JSON message."""
    # [FIX]: Testing the new /health endpoint instead of the old /
    response = test_client.get("/health") 
    assert response.status_code == 200
    assert response.get_json() == {"message": "Wormhole Queue System API is running"}


def test_404_for_unknown_route(test_client):
    response = test_client.get("/notreal")
    assert response.status_code == 404

# tests/test_auth.py
def test_login_route_exists(test_client):
    response = test_client.post("/api/login", json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code in [200, 401]  # Valid route, even if logic incomplete

