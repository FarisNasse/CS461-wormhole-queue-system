# tests/test_password_reset.py
from app import db
from app.models import User


def test_token_generation(test_app):
    """Test that a user can generate a valid JWT token."""
    with test_app.app_context():
        u = User(username="token_gen", email="gen@test.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

        token = u.get_reset_password_token()
        assert token is not None
        assert isinstance(token, str)


def test_token_verification(test_app):
    """Test that the token resolves back to the correct user."""
    with test_app.app_context():
        u = User(username="token_verify", email="verify@test.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

        token = u.get_reset_password_token()
        verified_user = User.verify_reset_password_token(token)

        assert verified_user is not None
        assert verified_user.id == u.id


def test_invalid_token_fails(test_app):
    """Test that a fake token returns None."""
    with test_app.app_context():
        result = User.verify_reset_password_token("garbage.token.string")
        assert result is None


def test_password_reset_request_route(test_client, test_app):
    """Test the Forgot Password page loads and handles valid email."""
    # 1. Setup User
    with test_app.app_context():
        u = User(username="reset_req", email="valid@test.com")
        u.set_password("old_pass")
        db.session.add(u)
        db.session.commit()

    # 2. Get Page
    resp = test_client.get("/reset_password_request")
    assert resp.status_code == 200
    assert b"Reset Password" in resp.data

    # 3. Post Valid Email
    # Note: We can't easily check the printed URL in a test,
    # but we can check for the success flash message or redirect.
    resp = test_client.post(
        "/reset_password_request",
        data={"email": "valid@test.com"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Check your email" in resp.data
