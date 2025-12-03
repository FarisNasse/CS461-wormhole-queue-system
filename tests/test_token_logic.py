from app import db
from app.models import User


def test_token_generation_and_verification(test_app):
    """
    Integration Test: Ensure a user can generate a token and retrieve their identity with it.
    """
    with test_app.app_context():
        # 1. Setup: Create a real user in the test database
        u = User(username="tokentest", email="token@test.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()

        # 2. Action: Generate the token
        token = u.get_reset_password_token()
        assert token is not None

        # 3. Verification: Decode the token to find the user
        verified_user = User.verify_reset_password_token(token)

        # 4. Assertions
        assert verified_user is not None
        assert verified_user.id == u.id
        assert verified_user.email == "token@test.com"


def test_expired_token_fails(test_app):
    """
    Unit/Logic Test: Ensure an expired token returns None.
    """
    with test_app.app_context():
        # Setup: Create a user object (doesn't strictly need DB for this specific failure path)
        u = User(username="expireduser", email="expired@test.com")
        u.id = 999  # Simulate an ID so the token payload has data

        # Action: Generate a token that expired 1 second ago
        token = u.get_reset_password_token(expires_in=-1)

        # Verification
        result = User.verify_reset_password_token(token)

        # Assertion: Should return None because it's expired
        assert result is None
