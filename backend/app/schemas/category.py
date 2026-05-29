from datetime import datetime
from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    url: str
    group_name: str | None
    parent_name: str | None
    last_crawled_at: datetime | None
    next_crawl_at: datetime | None
    brand_count: int = 0
    health_tag: str | None = None    # green / red / yellow
    health_note: str | None = None
    tags: list[str] | None = None    # 多维度标签

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    total: int
    items: list[CategoryResponse]


class ParentGroupResponse(BaseModel):
    """中类：包含多个小类"""
    parent_name: str | None
    categories: list[CategoryResponse]


class GroupResponse(BaseModel):
    """大类：包含多个中类"""
    group_name: str
    total_categories: int
    parents: list[ParentGroupResponse]


class GroupListResponse(BaseModel):
    groups: list[GroupResponse]
    ungrouped: list[CategoryResponse]  # group_name 为空的类别


class CategoryBrandsResponse(BaseModel):
    category_id: int
    category_name: str
    brands: list


class CrawlerStatusResponse(BaseModel):
    total_categories: int
    active_categories: int
    total_groups: int       # 大类数
    total_parents: int      # 中类数
    crawled_today: int
    pending_today: int
    total_brands: int
    last_discovery_at: str | None
    is_running: bool
