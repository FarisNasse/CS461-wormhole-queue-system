import os
import sys

import pytest

from app.models import User

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db


@pytest.fixture()
def test_app():
    app = create_app(testing=True)

    # FIX: Disable CSRF for tests so forms validate without tokens
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture()
def authenticated_client(test_client, test_app):
    """
    Returns a test client that is already logged in as a standard user.
    """
    with test_app.app_context():
        # Create user if not exists to prevent UniqueConstraint errors in repeated tests
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser", email="test@example.com", is_admin=False)
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

    test_client.post(
        "/api/login", json={"username": "testuser", "password": "password123"}
    )

    return test_client
