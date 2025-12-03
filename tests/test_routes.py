import pytest


def test_health_check_route(test_client):
    """Verify the health check endpoint returns 200 OK."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json == {"message": "Wormhole Queue System API is running"}


def test_home_page_loads(test_client):
    """Verify the root route '/' loads."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Wormhole" in response.data or b"Queue" in response.data


def test_assistant_login_page_loads(test_client):
    """Verify '/assistant-login' loads the Login Page with Form."""
    response = test_client.get("/assistant-login")
    assert response.status_code == 200
    # Check for the CSRF token to ensure the FlaskForm loaded correctly
    assert b'name="csrf_token"' in response.data


def test_dashboard_is_protected(test_client):
    """
    Verify that '/dashboard' redirects users who are NOT logged in.
    """
    response = test_client.get("/dashboard")
    # Expect 302 Found (Redirect) instead of 401
    assert response.status_code == 302
    # Ensure it redirects to the login page
    assert "/assistant-login" in response.headers["Location"]


def test_dashboard_access_granted(authenticated_client):
    """
    Verify that '/dashboard' allows users who ARE logged in.
    """
    response = authenticated_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_404_for_unknown_route(test_client):
    """Verify that unknown routes return 404."""
    response = test_client.get("/nonexistent-page")
    assert response.status_code == 404


def test_login_route_exists(test_client):
    """Verify the API login route handles GET requests gracefully (405)."""
    response = test_client.get("/api/login")
    assert response.status_code == 405
