# app/models.py
from datetime import UTC, datetime  # UPDATED: Added timezone
from time import time

import jwt
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    # FIXED: Use timezone-aware UTC default
    time_created = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=3600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
        return db.session.get(User, user_id)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    table = db.Column(db.String(50), nullable=False)
    physics_course = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Open", nullable=False)

    # FIXED: Use timezone-aware UTC default
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    time_resolved = db.Column(db.DateTime, nullable=True)
    number_of_students = db.Column(db.Integer, nullable=True)
    wa_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "table_number": self.table,
            "class_name": self.physics_course,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))
