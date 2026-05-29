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
    updated_at: datetime | None

    model_config = {"from_attributes": True}
