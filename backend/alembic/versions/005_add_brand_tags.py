"""add tags and note to brands

Revision ID: 005
Revises: 004
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("brands", sa.Column("tags", sa.JSON(), nullable=True))
    op.add_column("brands", sa.Column("brand_note", sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column("brands", "brand_note")
    op.drop_column("brands", "tags")
