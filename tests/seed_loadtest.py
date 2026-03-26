# tests/seed_loadtest.py
import os
import sys

# 1. Path modification to find the 'app' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db  # noqa: E402
from app.models import User     # noqa: E402

def seed_loadtest_user():
    """Seeds the database with a test assistant account for load testing."""
    app = create_app()
    
    with app.app_context():
        username = os.getenv("LOCUST_ASSISTANT_USERNAME", "ci_test_assistant")
        password = os.getenv("LOCUST_ASSISTANT_PASSWORD", "ci_test_password")
        
        existing_user = db.session.query(User).filter_by(username=username).first()
        
        if not existing_user:
            print(f"Creating load-test user: {username}")
            test_user = User(
                username=username,
                email=f"{username}@wormhole.loadtest",
                name="Load Test Assistant",
                is_admin=False,
                is_active=True
            )
            test_user.set_password(password)
            db.session.add(test_user)
            db.session.commit()
            print("User created successfully.")
        else:
            print(f"User '{username}' already exists. Skipping creation.")

if __name__ == "__main__":
    seed_loadtest_user()