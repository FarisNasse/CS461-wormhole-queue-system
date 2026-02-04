# tests/conftest.py
import os
import sys

import pytest

# 1. Path modification MUST come before importing 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 2. Use '# noqa: E402' to tell Ruff this order is intentional
from app import create_app, db  # noqa: E402


@pytest.fixture()
def test_app():
    """Creates a Flask app instance for testing."""
    app = create_app(testing=True)

    # Disable CSRF protection for testing
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def test_client(test_app):
    """A test client for the app."""
    return test_app.test_client()
