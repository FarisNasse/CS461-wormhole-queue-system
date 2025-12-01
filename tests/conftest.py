# tests/conftest.py
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app, db


@pytest.fixture()
def test_app():
    app = create_app(testing=True)
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
def auth_client(test_client):
    """A helper to create a user and log them in easily."""
    # Create a user
    user = User(username="testuser", email="test@test.com", is_admin=True)
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    # Log them in using the API endpoint you built
    test_client.post(
        "/api/login", json={"username": "testuser", "password": "password"}
    )
    return test_client
