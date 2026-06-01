import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.models.brand_rank_history import BrandRankHistory

logger = logging.getLogger(__name__)


async def _get_brand_annotation(db: AsyncSession, name: str) -> tuple[list | None, str | None]:
    """从同名品牌中查找已有的标签和说明，用于新品牌自动继承。"""
    result = await db.execute(
        select(Brand.tags, Brand.brand_note)
        .where(Brand.name == name, Brand.tags.isnot(None))
        .limit(1)
    )
    row = result.first()
    if row:
        return row.tags, row.brand_note
    return None, None


async def upsert_brands(db: AsyncSession, category_id: int, brands_data: list[dict]) -> None:
    """Insert or update brands for a category, tracking rank changes.

    新品牌自动从同名品牌继承 tags 和 brand_note。
    每次爬取后记录排名快照到 brand_rank_history，供趋势图使用。
    """
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
            # 如果当前没有标签，尝试从同名品牌继承
            if not existing.tags:
                tags, note = await _get_brand_annotation(db, name)
                if tags:
                    existing.tags = tags
                    existing.brand_note = note
        else:
            # 新品牌：自动从同名品牌继承标签
            tags, note = await _get_brand_annotation(db, name)
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
                    tags=tags,
                    brand_note=note,
                )
            )
            if tags:
                logger.info("New brand %s inherited tags: %s", name, tags)
            else:
                logger.info("New brand added: %s in category %d at rank %d", name, category_id, data.get("rank", 0))

    # flush 确保新品牌获得 id，然后批量写排名历史快照
    await db.flush()
    now = datetime.now()
    brands_result = await db.execute(
        select(Brand).where(Brand.category_id == category_id)
    )
    for brand in brands_result.scalars().all():
        db.add(BrandRankHistory(
            brand_id=brand.id,
            category_id=category_id,
            rank=brand.rank,
            recorded_at=now,
        ))

    await db.commit()
