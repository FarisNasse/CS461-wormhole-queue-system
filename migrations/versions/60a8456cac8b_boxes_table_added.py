"""boxes table added

Revision ID: 60a8456cac8b
Revises: 9d200740c874
Create Date: 2026-04-29 18:46:18.247936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '60a8456cac8b'
down_revision = '9d200740c874'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('boxes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('box_name', sa.String(length=100), nullable=False),
    sa.Column('battery_status', sa.String(length=50), nullable=False),
    sa.Column('update_time', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('boxes')
