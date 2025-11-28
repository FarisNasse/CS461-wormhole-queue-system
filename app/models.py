# app/models.py
"""
Module Name: models.py

Defines User and Ticket database models using SQLAlchemy ORM.
Updated to support Flask-Login and provide legacy template compatibility.
"""

from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # [NEW] Required for Flask-Login

from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, autoincrement=True)
    username: orm.Mapped[str] = orm.mapped_column(sa.String(100), unique=True, index=True)
    email: orm.Mapped[str] = orm.mapped_column(sa.String(100), unique=True, index=True)
    password_hash: orm.Mapped[Optional[str]] = orm.mapped_column(sa.String(128))
    is_admin: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)
    time_created: orm.Mapped[datetime] = orm.mapped_column(
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
    
    # [Flask-Login] Optional explicit override (UserMixin does this by default, but this is safe)
    def get_id(self):
        return str(self.id)

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, autoincrement=True)
    student_name: orm.Mapped[str] = orm.mapped_column(sa.String(100))
    table: orm.Mapped[str] = orm.mapped_column(sa.String(50))
    physics_course: orm.Mapped[str] = orm.mapped_column(sa.String(50))
    status: orm.Mapped[str] = orm.mapped_column(sa.String(20), index=True, default='live')
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    time_resolved: orm.Mapped[Optional[datetime]] = orm.mapped_column(
        default=None
    )
    number_of_students: orm.Mapped[Optional[int]] = orm.mapped_column(default=1)
    wa_id: orm.Mapped[Optional[int]] = orm.mapped_column(
        sa.ForeignKey('users.id'), default=None, index=True
    )
    wormhole_assistant: orm.Mapped[Optional[User]] = orm.relationship(back_populates="tickets")

    # --- COMPATIBILITY LAYER (Shims for Legacy Templates) ---
    # These properties allow old templates to use old names without breaking.
    
    @property
    def name(self):
        return self.student_name

    @property
    def phClass(self):
        return self.physics_course

    @property
    def time_create(self):
        return self.created_at

    # --------------------------------------------------------

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
        }
    
    def mark_resolved(self, user: Optional['User'] = None):
        self.status = 'resolved'
        self.time_resolved = datetime.now(timezone.utc)
        if user and self.wa_id is None:
            self.assign_to(user)
        db.session.commit()

    def assign_to(self, user: 'User'):
        """Assign ticket to a user."""
        self.wa_id = user.id
        db.session.commit()