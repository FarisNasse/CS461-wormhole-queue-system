import pytest
import time
import jwt
from unittest.mock import patch
from flask import current_app
from app import db
from app.models import User
from app.forms import ResetPasswordRequestForm, ResetPasswordForm

def test_password_hashing(test_app):
    """Ensure password hashing works before testing resets."""
    with test_app.app_context():
        u = User(username='hash_test', email='hash@test.com')
        u.set_password('cat')
        assert u.check_password('cat')
        assert not u.check_password('dog')

def test_get_reset_password_token(test_app):
    """Test that a user can generate a valid JWT token."""
    with test_app.app_context():
        user = User(username='token_user', email='token@example.com')
        db.session.add(user)
        db.session.commit()

        # Updated: Using the correct method name from models.py
        token = user.get_reset_password_token()
        assert token is not None
        
        # Verify the token decodes back to the user
        verified_user = User.verify_reset_password_token(token)
        assert verified_user.id == user.id

def test_reset_request_page_loads(test_client):
    """Test that the Request Reset page loads successfully (GET)."""
    response = test_client.get('/reset_password_request')
    assert response.status_code == 200
    assert b'Reset Password' in response.data

def test_reset_email_sending_mocked(test_client, test_app):
    """Test that submitting the form calls the email utility."""
    with test_app.app_context():
        user = User(username='email_user', email='sendme@example.com')
        db.session.add(user)
        db.session.commit()

    # MOCK: Since we use AWS SES/Boto3, we mock the utility function
    # instead of checking a flask-mail outbox.
    with patch('app.routes.auth.send_password_reset_email') as mock_send:
        response = test_client.post('/reset_password_request', data={
            'email': 'sendme@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Check your email" in response.data
        # Verify our email utility was actually triggered
        assert mock_send.called

def test_verify_invalid_token(test_app):
    """Test that bad tokens return None."""
    with test_app.app_context():
        user = User.verify_reset_password_token('this-is-not-a-valid-jwt-token')
        assert user is None

def test_verify_expired_token(test_app):
    """Test that an expired JWT token is rejected."""
    with test_app.app_context():
        u = User(username="expiretest", email="expire@test.com")
        db.session.add(u)
        db.session.commit()
        
        # Manually create a token that is already expired
        expired_payload = {"reset_password": u.id, "exp": time.time() - 10}
        token = jwt.encode(
            expired_payload, 
            current_app.config["SECRET_KEY"], 
            algorithm="HS256"
        )
            
        verified_user = User.verify_reset_password_token(token)
        assert verified_user is None

def test_reset_password_workflow(test_client, test_app):
    """
    FULL INTEGRATION TEST:
    1. Generate a token for a user.
    2. Use that token to access the reset page.
    3. Submit a new password.
    4. Verify the password changed in the DB.
    """
    with test_app.app_context():
        user = User(username='reset_flow', email='flow@example.com')
        user.set_password('old_password')
        db.session.add(user)
        db.session.commit()
        
        token = user.get_reset_password_token()

    # 1. Access the reset page with the token
    response = test_client.get(f'/reset_password/{token}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Reset Password' in response.data

    # 2. Post new password
    # Disable CSRF for testing purposes if not already handled in conftest
    test_app.config['WTF_CSRF_ENABLED'] = False
    
    response = test_client.post(f'/reset_password/{token}', data={
        'password': 'new_secure_password',
        'confirm_password': 'new_secure_password'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Your password has been reset' in response.data

    # 3. Verify Database Update
    with test_app.app_context():
        updated_user = db.session.get(User, user.id)
        assert updated_user.check_password('new_secure_password')
        assert not updated_user.check_password('old_password')