"""add brand_rank_history table

Revision ID: 006
Revises: 005
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brand_rank_history",
        sa.Column("id",          sa.Integer(), primary_key=True),
        sa.Column("brand_id",    sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("rank",        sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_rank_hist_brand", "brand_rank_history", ["brand_id", "recorded_at"])
    op.create_index("idx_rank_hist_cat",   "brand_rank_history", ["category_id", "recorded_at"])


def downgrade() -> None:
    op.drop_index("idx_rank_hist_cat",   table_name="brand_rank_history")
    op.drop_index("idx_rank_hist_brand", table_name="brand_rank_history")
    op.drop_table("brand_rank_history")
