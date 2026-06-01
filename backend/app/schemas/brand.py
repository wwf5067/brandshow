from datetime import datetime
from pydantic import BaseModel


class BrandResponse(BaseModel):
    id: int
    rank: int
    prev_rank: int | None
    name: str
    brand_index: int | None
    likes: int | None
    logo_url: str | None
    detail_url: str | None
    company_name: str | None
    tags: list[str] | None = None
    brand_note: str | None = None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class RankHistoryItem(BaseModel):
    rank: int
    recorded_at: datetime

    model_config = {"from_attributes": True}


class TaggedBrandCategoryInfo(BaseModel):
    id: int
    name: str
    group_name: str | None
    parent_name: str | None

    model_config = {"from_attributes": True}


class TaggedBrandItem(BaseModel):
    brand_id: int
    name: str
    rank: int
    logo_url: str | None
    tags: list[str] | None
    brand_note: str | None
    category: TaggedBrandCategoryInfo
