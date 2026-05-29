import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    prev_rank = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    brand_index = Column(Integer, nullable=True)
    likes = Column(Integer, nullable=True)
    logo_url = Column(String(500), nullable=True)
    detail_url = Column(String(500), nullable=True)
    company_name = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    category = relationship("Category", back_populates="brands")

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_category_brand"),
    )
