import os
import sys
import pytest

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
# IMPORTANT: Import models here to register them with SQLAlchemy
from app.models import User, Ticket 

@pytest.fixture()
def test_app():
    app = create_app(testing=True)

    with app.app_context():
        db.create_all()  # Now definitely creates tables in test.db
        
        yield app  # Run the test
        
        db.session.remove()
        db.drop_all()

    # Cleanup: Delete the file after tests run
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except PermissionError:
            pass

@pytest.fixture()
def test_client(test_app):
    return test_app.test_client()