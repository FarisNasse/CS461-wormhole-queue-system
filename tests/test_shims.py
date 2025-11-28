# tests/test_shims.py
def test_shim_login_redirects(test_client):
    """Ensure /shim/login redirects to the real assistant login."""
    response = test_client.get("/shim/login")
    assert response.status_code == 302
    assert "/assistant-login" in response.location

def test_shim_index_redirects(test_client):
    """Ensure /shim/index redirects to the real home page."""
    response = test_client.get("/shim/index")
    assert response.status_code == 302
    assert "/" in response.location or "/index" in response.location

def test_shim_create_ticket_redirects(test_client):
    """Ensure the legacy create ticket link redirects to the new route."""
    response = test_client.get("/shim/createhelprequest")
    assert response.status_code == 302
    assert "/create-ticket" in response.location

def test_shim_userpage_redirects(test_client):
    """Ensure the legacy userpage link redirects to profile."""
    # The shim takes a username argument, so we provide one
    response = test_client.get("/shim/userpage/someuser")
    assert response.status_code == 302
    assert "/profile" in response.location