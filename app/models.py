#app/models.py
"""
Module Name: models.py

A python module that describes the database models.

Defines User and Ticket database models using SQLAlchemy ORM.

Typical usage example:
    from app import models
"""

from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer


class User(db.Model):
    __tablename__ = 'users'
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, autoincrement=True)
    username: orm.Mapped[str] = orm.mapped_column(sa.String(100))
    email: orm.Mapped[str] = orm.mapped_column(sa.String(100), unique=True, index=True)
    password_hash: orm.Mapped[Optional[str]] = orm.mapped_column(sa.String(128))
    is_admin: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    tickets: orm.WriteOnlyMapped['Ticket'] = orm.relationship(back_populates="wormhole_assistant")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def claim_ticket(self, ticket: 'Ticket') -> bool:
        if ticket.wa_id is None:
            ticket.assign_to(self)
            return True
        return False
    
    def get_reset_token(self, expires_sec=1800):
        """Generate a secure token valid for 30 minutes for password reset."""
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token):
        """Verify a password reset token and return the associated user (stub implementation)."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='password-reset-salt', max_age=1800)['user_id']
        except:
            return None
        return db.session.get(User, user_id)
    
class Ticket(db.Model):
    __tablename__ = 'tickets'
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, autoincrement=True)
    student_name: orm.Mapped[str] = orm.mapped_column(sa.String(100))
    table: orm.Mapped[str] = orm.mapped_column(sa.String(50))
    physics_course: orm.Mapped[str] = orm.mapped_column(sa.String(50))
    status: orm.Mapped[str] = orm.mapped_column(sa.String(20), default='live')
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    closed_at: orm.Mapped[Optional[datetime]] = orm.mapped_column(
        default=None
    )
    closed_reason: orm.Mapped[Optional[str]] = orm.mapped_column(sa.String(20), default=None)
    # closed reason can be 'helped', 'no_show', 'duplicate', 'flushed'
    
    number_of_students: orm.Mapped[Optional[int]] = orm.mapped_column(default=1)
    wa_id: orm.Mapped[Optional[int]] = orm.mapped_column(
        sa.ForeignKey('users.id'), default=None, index=True
    )
    wormhole_assistant: orm.Mapped[Optional[User]] = orm.relationship(back_populates="tickets")

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, student_name={self.student_name}, status={self.status})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "table": self.table,
            "physics_course": self.physics_course,
            "status": self.status,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "closed_reason": self.closed_reason,
            "number_of_students": self.number_of_students,
            "wa_id": self.wa_id,
        }
    
    def close_ticket(self, closed_reason, num_students: Optional[int] = 1):
        self.status = 'closed'
        self.number_of_students = num_students
        self.closed_reason = closed_reason
        self.time_resolved = datetime.now(timezone.utc)
        db.session.commit()

    def assign_to(self, user: 'User'):
        """Assign ticket to a user."""
        self.wa_id = user.id
        db.session.commit()
    
# Old models for reference

# class Ticket(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     student_name = db.Column(db.String(80))
#     table_number = db.Column(db.String(10))
#     class_name = db.Column(db.String(50))
#     status = db.Column(db.String(50), default="Open")
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     deactivated_at = db.Column(db.DateTime, nullable=True)
#     num_students = db.Column(db.Integer, nullable=True)
#     current_ta = db.Column(db.String(80), nullable=True)

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(64), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(128), nullable=False)
#     is_admin = db.Column(db.Boolean, default=False)