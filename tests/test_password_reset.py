import pytest
from app import db, mail
from app.models import User

def test_password_hashing(test_app):
    """Ensure password hashing works before testing resets."""
    with test_app.app_context():
        u = User(username='hash_test', email='hash@test.com')
        u.set_password('cat')
        assert u.check_password('cat')
        assert not u.check_password('dog')

def test_get_reset_token(test_app):
    """Test that a user can generate a valid token."""
    with test_app.app_context():
        user = User(username='token_user', email='token@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        token = user.get_reset_token()
        assert token is not None
        
        # Verify the token decodes back to the user
        verified_user = User.verify_reset_token(token)
        assert verified_user.id == user.id

def test_verify_invalid_token(test_app):
    """Test that bad tokens return None."""
    with test_app.app_context():
        user = User.verify_reset_token('invalid_token_string')
        assert user is None

def test_reset_request_page(test_client):
    """Test that the Request Reset page loads successfully (GET)."""
    response = test_client.get('/reset_password_request')
    assert response.status_code == 200
    assert b'Reset Password' in response.data

def test_reset_email_sending(test_client, test_app):
    """Test submitting the form sends an email with a link."""
    with test_app.app_context():
        # 1. Setup a user
        user = User(username='email_user', email='sendme@example.com')
        user.set_password('oldpass')
        db.session.add(user)
        db.session.commit()

        # 2. Mock the mail sending to capture the outgoing email
        with mail.record_messages() as outbox:
            response = test_client.post('/reset_password_request', data={
                'email': 'sendme@example.com'
            }, follow_redirects=True)

            # 3. Assertions
            assert response.status_code == 200
            assert len(outbox) == 1  # Verify one email was sent
            assert outbox[0].subject == "Reset Your Password"
            assert outbox[0].recipients == ["sendme@example.com"]
            
            # Check if the body contains a link (basic check)
            assert "http://" in outbox[0].body or "https://" in outbox[0].body
            assert "reset_password/" in outbox[0].body

def test_reset_password_workflow(test_client, test_app):
    """
    FULL INTEGRATION TEST:
    1. Generate a token for a user.
    2. Use that token to access the reset page.
    3. Submit a new password.
    4. Verify the password changed in the DB.
    """
    with test_app.app_context():
        # Setup
        user = User(username='reset_flow', email='flow@example.com')
        user.set_password('old_password')
        db.session.add(user)
        db.session.commit()
        
        # Manually generate token to simulate clicking the email link
        token = user.get_reset_token()

    # 1. Access the reset page with the token
    response = test_client.get(f'/reset_password/{token}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Reset Password' in response.data

    # 2. Post new password
    response = test_client.post(f'/reset_password/{token}', data={
        'password': 'new_secure_password',
        'confirm_password': 'new_secure_password'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Should be redirected to login page with success message
    assert b'Your password has been updated' in response.data

    # 3. Verify Database Update
    with test_app.app_context():
        updated_user = User.query.filter_by(email='flow@example.com').first()
        assert updated_user.check_password('new_secure_password')
        assert not updated_user.check_password('old_password')

def test_reset_with_invalid_email(test_client, test_app):
    """Security Test: Ensure we don't crash or reveal info if email is wrong."""
    with mail.record_messages() as outbox:
        response = test_client.post('/reset_password_request', data={
            'email': 'nonexistent@example.com'
        }, follow_redirects=True)

        # Should still redirect to login to prevent "Email Enumeration"
        # (i.e. don't tell the hacker "This email doesn't exist")
        assert response.status_code == 200
        assert b'Check your email' in response.data
        
        # Crucial: Ensure NO email was sent
        assert len(outbox) == 0