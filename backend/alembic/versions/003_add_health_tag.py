"""add health_tag and health_note to categories

Revision ID: 003
Revises: 002
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("health_tag", sa.String(10), nullable=True))
    op.add_column("categories", sa.Column("health_note", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("categories", "health_note")
    op.drop_column("categories", "health_tag")
