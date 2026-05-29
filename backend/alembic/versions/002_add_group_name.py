"""add group_name to categories

Revision ID: 002
Revises: 001
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("group_name", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("categories", "group_name")
