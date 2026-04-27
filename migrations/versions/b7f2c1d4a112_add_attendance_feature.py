"""add attendance feature

Revision ID: b7f2c1d4a112
Revises: 9d200740c874
Create Date: 2026-04-23 23:45:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7f2c1d4a112"
down_revision = "9d200740c874"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attendance_shifts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("attendance_shifts", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_attendance_shifts_created_at"),
            ["created_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_shifts_day_of_week"),
            ["day_of_week"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_shifts_user_id"),
            ["user_id"],
            unique=False,
        )

    op.create_table(
        "attendance_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("checked_out_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("check_in_source", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["shift_id"], ["attendance_shifts.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("attendance_sessions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_attendance_sessions_checked_in_at"),
            ["checked_in_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_sessions_last_seen_at"),
            ["last_seen_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_sessions_shift_id"),
            ["shift_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_sessions_status"),
            ["status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_sessions_user_id"),
            ["user_id"],
            unique=False,
        )

    op.create_table(
        "attendance_activities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("attendance_session_id", sa.Integer(), nullable=True),
        sa.Column("ticket_id", sa.Integer(), nullable=True),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attendance_session_id"], ["attendance_sessions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("attendance_activities", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_attendance_activities_activity_type"),
            ["activity_type"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_activities_attendance_session_id"),
            ["attendance_session_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_activities_created_at"),
            ["created_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_activities_ticket_id"),
            ["ticket_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_attendance_activities_user_id"),
            ["user_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("attendance_activities", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_attendance_activities_user_id"))
        batch_op.drop_index(batch_op.f("ix_attendance_activities_ticket_id"))
        batch_op.drop_index(batch_op.f("ix_attendance_activities_created_at"))
        batch_op.drop_index(
            batch_op.f("ix_attendance_activities_attendance_session_id")
        )
        batch_op.drop_index(batch_op.f("ix_attendance_activities_activity_type"))
    op.drop_table("attendance_activities")

    with op.batch_alter_table("attendance_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_attendance_sessions_user_id"))
        batch_op.drop_index(batch_op.f("ix_attendance_sessions_status"))
        batch_op.drop_index(batch_op.f("ix_attendance_sessions_shift_id"))
        batch_op.drop_index(batch_op.f("ix_attendance_sessions_last_seen_at"))
        batch_op.drop_index(batch_op.f("ix_attendance_sessions_checked_in_at"))
    op.drop_table("attendance_sessions")

    with op.batch_alter_table("attendance_shifts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_attendance_shifts_user_id"))
        batch_op.drop_index(batch_op.f("ix_attendance_shifts_day_of_week"))
        batch_op.drop_index(batch_op.f("ix_attendance_shifts_created_at"))
    op.drop_table("attendance_shifts")
