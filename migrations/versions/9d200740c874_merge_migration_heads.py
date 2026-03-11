"""merge migration heads

Revision ID: 9d200740c874
Revises: cc45944c4dda, f3188ae0a966
Create Date: 2026-03-11 14:39:44.414533

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d200740c874'
down_revision = ('cc45944c4dda', 'f3188ae0a966')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
