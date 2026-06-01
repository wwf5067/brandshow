import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from app.database import Base


class BrandRankHistory(Base):
    __tablename__ = "brand_rank_history"

    id          = Column(Integer, primary_key=True)
    brand_id    = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, nullable=False)
    rank        = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_rank_hist_brand", "brand_id", "recorded_at"),
        Index("idx_rank_hist_cat",   "category_id", "recorded_at"),
    )
