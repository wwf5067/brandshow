import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand

logger = logging.getLogger(__name__)


async def upsert_brands(db: AsyncSession, category_id: int, brands_data: list[dict]) -> None:
    """Insert or update brands for a category, tracking rank changes."""
    for data in brands_data:
        name = data.get("name", "").strip()
        if not name:
            continue

        result = await db.execute(
            select(Brand).where(Brand.category_id == category_id, Brand.name == name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            new_rank = data.get("rank", existing.rank)
            if existing.rank != new_rank:
                existing.prev_rank = existing.rank
                existing.rank = new_rank
                logger.info("Rank change: %s in category %d: %d → %d", name, category_id, existing.rank, new_rank)
            existing.brand_index = data.get("brand_index")
            existing.likes = data.get("likes")
            if data.get("logo_url"):
                existing.logo_url = data["logo_url"]
            if data.get("detail_url"):
                existing.detail_url = data["detail_url"]
            if data.get("company_name"):
                existing.company_name = data["company_name"]
        else:
            db.add(
                Brand(
                    category_id=category_id,
                    rank=data.get("rank", 0),
                    name=name,
                    brand_index=data.get("brand_index"),
                    likes=data.get("likes"),
                    logo_url=data.get("logo_url"),
                    detail_url=data.get("detail_url"),
                    company_name=data.get("company_name"),
                )
            )
            logger.info("New brand added: %s in category %d at rank %d", name, category_id, data.get("rank", 0))

    await db.commit()
