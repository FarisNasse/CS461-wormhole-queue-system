def test_reset_request_page_loads(test_client):
    """Stage 1: Ensure the email request page loads."""
    response = test_client.get("/reset_password_request")
    assert response.status_code == 200
    assert b"Reset Password" in response.data


def test_reset_request_submission(test_client, test_app):
    """
    Stage 1: Ensure submitting a valid email flashes the success message.
    """
    # FAANG Trick: Temporarily disable CSRF validation for this specific test
    # so we can focus on testing the Business Logic (Email flow) without
    # needing to parse HTML tokens.
    test_app.config["WTF_CSRF_ENABLED"] = False

    response = test_client.post(
        "/reset_password_request",
        data={"email": "nonexistent@example.com"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Security check: The message should be generic to avoid user enumeration
    assert b"Check your email" in response.data

    # Good practice: Re-enable it afterwards (though pytest fixture cleanup usually handles this)
    test_app.config["WTF_CSRF_ENABLED"] = True


def test_reset_password_route_requires_token(test_client):
    """
    Stage 2: Ensure accessing the reset route without a token (or with invalid path) fails.
    """
    # Attempt to hit the route structure without a token
    response = test_client.get("/reset_password/")
    assert response.status_code == 404
