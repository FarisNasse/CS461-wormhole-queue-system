# app/models.py
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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class _ModelQueryProperty:
    """
    Descriptor that provides the legacy-style `Model.query` attribute.
    Ensures that User.query and Ticket.query continue to work with DeclarativeBase.
    """

    def __get__(self, instance, owner):
        if owner is None:
            return self
        return db.session.query(owner)


class Base(DeclarativeBase):
    """
    Base class for all models.

    We explicitly bind this to db.metadata so Flask-Migrate can detect changes.
    We also add the query property so legacy queries (User.query.filter...) work.
    """

    metadata = db.metadata
    query = db.session.query_property()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(sa.String(100), nullable=True)
    username: Mapped[str] = mapped_column(sa.String(100), unique=True)
    email: Mapped[str] = mapped_column(sa.String(100), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(sa.String(128))
    is_admin: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tickets: orm.WriteOnlyMapped["Ticket"] = orm.relationship(
        back_populates="wormhole_assistant"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def claim_ticket(self, ticket: "Ticket") -> bool:
        if ticket.wa_id is None:
            ticket.assign_to(self)
            return True
        return False


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_name: Mapped[str] = mapped_column(sa.String(100))
    table: Mapped[str] = mapped_column(sa.String(50))
    physics_course: Mapped[str] = mapped_column(sa.String(50))
    status: Mapped[str] = mapped_column(sa.String(20), default="live")
    created_at: Mapped[datetime] = mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    closed_reason: Mapped[Optional[str]] = mapped_column(sa.String(20), default=None)

    number_of_students: Mapped[Optional[int]] = mapped_column(default=1)

    # Foreign Keys
    wa_id: Mapped[Optional[int]] = mapped_column(
        sa.ForeignKey("users.id"), default=None, index=True
    )

    # Relationships
    wormhole_assistant: Mapped[Optional["User"]] = orm.relationship(
        back_populates="tickets"
    )

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
        self.status = "closed"
        self.number_of_students = num_students
        self.closed_reason = closed_reason
        self.closed_at = datetime.now(timezone.utc)
        db.session.commit()

    def assign_to(self, user: "User"):
        """Assign ticket to a user."""
        self.wa_id = user.id
        self.status = "in_progress"
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
