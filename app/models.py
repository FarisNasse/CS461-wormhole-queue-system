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
import sqlalchemy.orm as orm
from app import db

class User(db.Model):
    __tablename__ = 'users'
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    username: orm.Mapped[str] = orm.mapped_column(sa.String(100))
    email: orm.Mapped[str] = orm.mapped_column(sa.String(100), unique=True, index=True)
    password_hash: orm.Mapped[str] = orm.mapped_column(sa.String(128))
    is_admin: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)
    time_created: orm.Mapped[datetime] = orm.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    tickets: orm.WriteOnlyMapped['Ticket'] = orm.relationship(back_populates="wormhole_assistant")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    student_name: orm.Mapped[str] = orm.mapped_column(sa.String(100))
    table: orm.Mapped[str] = orm.mapped_column(sa.String(50))
    physics_course: orm.Mapped[str] = orm.mappped_column(sa.String(50))
    status: orm.Mapped[str] = orm.mapped_column(sa.String(20), index=True, default='live')
    time_created: orm.Mapped[datetime] = orm.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    time_resolved: orm.Mappped[Optional[datetime]] = orm.mapped_column(
        default=None
    )
    number_of_students: orm.Mapped[Optional[int]] = orm.mapped_column(default=1)
    wa_id: orm.Mapped[Optional[int]] = orm.mapped_column(
        sa.ForeignKey('users.id'), default=None, index=True
    )
    wormhole_assistant: orm.Mapped[User] = orm.relationship(back_populates="tickets")

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, student_name={self.student_name}, status={self.status})>"