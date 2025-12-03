import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User


def test_prevent_duplicate_emails(test_app):
    """
    Constraint Test: Database should throw an error if two users share an email.
    """
    with test_app.app_context():
        # User 1
        u1 = User(username="user1", email="unique@example.com")
        u1.set_password("pass")
        db.session.add(u1)
        db.session.commit()

        # User 2 (Same Email)
        u2 = User(username="user2", email="unique@example.com")
        u2.set_password("pass")
        db.session.add(u2)

        # Assert that the commit fails
        with pytest.raises(IntegrityError):
            db.session.commit()

        # Clean up session (rollback is usually automatic in failure, but good practice)
        db.session.rollback()


def test_prevent_duplicate_usernames(test_app):
    """
    Constraint Test: Database should throw an error if two users share a username.
    """
    with test_app.app_context():
        u1 = User(username="same_name", email="email1@example.com")
        u1.set_password("pass")
        db.session.add(u1)
        db.session.commit()

        u2 = User(username="same_name", email="email2@example.com")
        u2.set_password("pass")
        db.session.add(u2)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
