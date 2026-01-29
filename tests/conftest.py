# tests/conftest.py
import os
import sys

import pytest

from app import create_app, db

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture()
def test_app():
    app = create_app(testing=True)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def test_client(test_app):
    return test_app.test_client()
