"""add site content editor

Revision ID: af3c2d4e5f61
Revises: 9d200740c874
Create Date: 2026-05-13 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "af3c2d4e5f61"
down_revision = "9d200740c874"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "site_content",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("key"),
    )
    with op.batch_alter_table("site_content", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_site_content_updated_by_id"),
            ["updated_by_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("site_content", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_site_content_updated_by_id"))

    op.drop_table("site_content")
