"""add tags to categories

Revision ID: 004
Revises: 003
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tags: JSON array of strings, e.g. ["essential", "healthy"]
    op.add_column("categories", sa.Column("tags", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("categories", "tags")
