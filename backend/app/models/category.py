import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    parent_name = Column(String(200), nullable=True)
    group_name = Column(String(200), nullable=True)   # 大类，如"手机数码"
    last_crawled_at = Column(DateTime, nullable=True)
    next_crawl_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    brands = relationship("Brand", back_populates="category", cascade="all, delete-orphan")
