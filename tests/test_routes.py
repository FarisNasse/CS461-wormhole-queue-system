from app.models import User
from app import db

def test_health_check_route(test_client):
    """Test the /health route returns 200 and the correct JSON message."""
    response = test_client.get("/health") 
    assert response.status_code == 200
    assert response.get_json() == {"message": "Wormhole Queue System API is running"}

def test_home_page_loads(test_client):
    """Verify the root route '/' loads the Student Home Page."""
    response = test_client.get("/")
    assert response.status_code == 200
    # [FIX] Updated text to match Jonathan's index.html
    assert b"For Students" in response.data

def test_assistant_login_page_loads(test_client):
    """Verify '/assistant-login' loads the Login Page."""
    response = test_client.get("/assistant-login")
    assert response.status_code == 200
    assert b"System Login" in response.data

def test_dashboard_is_protected(test_client):
    """Verify that '/dashboard' blocks users who are NOT logged in."""
    response = test_client.get("/dashboard")
    assert response.status_code == 302 
    assert "/assistant-login" in response.location

def test_dashboard_access_granted(test_client, test_app):
    """Verify logged-in user can access dashboard."""
    with test_app.app_context():
        u = User(username="dash_user", email="d@d.com", is_admin=False)
        u.set_password("password")
        db.session.add(u)
        db.session.commit()

    test_client.post("/api/login", json={
        "username": "dash_user", 
        "password": "password"
    })

    response = test_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Profile" in response.data
    assert b"dash_user" in response.data

def test_404_for_unknown_route(test_client):
    response = test_client.get("/notreal")
    assert response.status_code == 404