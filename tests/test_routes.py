# tests/test_routes.py
from flask import session

def test_health_check_route(test_client):
    """Test the /health route returns 200 and the correct JSON message."""
    response = test_client.get("/health") 
    assert response.status_code == 200
    assert response.get_json() == {"message": "Wormhole Queue System API is running"}

def test_home_page_loads(test_client):
    """
    Verify the root route '/' loads the Student Home Page (index.html).
    We check for specific text that only exists in index.html.
    """
    response = test_client.get("/")
    assert response.status_code == 200
    # Check for text specific to your index.html file
    assert b"Physics Collaboration and Help Center" in response.data

def test_assistant_login_page_loads(test_client):
    """
    Verify '/assistant-login' loads the Login Page (login.html).
    We check for the form elements to ensure the right template rendered.
    """
    response = test_client.get("/assistant-login")
    assert response.status_code == 200
    # Check for the specific form title or button in login.html
    assert b"System Login" in response.data
    assert b"Sign In" in response.data

def test_dashboard_is_protected(test_client):
    """
    Verify that '/dashboard' blocks users who are NOT logged in.
    Should return 401 (Unauthorized).
    """
    response = test_client.get("/dashboard")
    assert response.status_code == 401
    # Check that we get the JSON error from your @login_required decorator
    assert response.get_json() == {"error": "Authentication required"}

def test_dashboard_access_granted(test_client):
    """
    Verify that '/dashboard' allows users who ARE logged in.
    We simulate a login by manually setting the session cookie.
    """
    # 1. Simulate a logged-in user by setting the session
    with test_client.session_transaction() as sess:
        sess['user_id'] = 1  # Fake user ID
        sess['is_admin'] = False

    # 2. Try to access the dashboard
    response = test_client.get("/dashboard")

    # 3. Expect success
    assert response.status_code == 200
    assert b"Welcome! You are logged in" in response.data

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

