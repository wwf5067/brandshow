from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brand import Brand
from app.models.category import Category

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("/search")
async def search_brands(
    name: str = Query(..., min_length=1, description="品牌名关键词"),
    db: AsyncSession = Depends(get_db),
):
    """输入品牌名，返回该品牌出现在哪些类别的 Top10 排行榜中。"""
    result = await db.execute(
        select(Brand, Category)
        .join(Category, Brand.category_id == Category.id)
        .where(Brand.name.ilike(f"%{name}%"))
        .order_by(Brand.rank)
    )
    rows = result.all()

    # 按品牌名精确度排序：完全匹配排前面
    items = []
    for brand, cat in rows:
        items.append({
            "brand_id": brand.id,
            "brand_name": brand.name,
            "rank": brand.rank,
            "prev_rank": brand.prev_rank,
            "logo_url": brand.logo_url,
            "detail_url": brand.detail_url,
            "company_name": brand.company_name,
            "updated_at": brand.updated_at,
            "category": {
                "id": cat.id,
                "name": cat.name,
                "group_name": cat.group_name,
                "parent_name": cat.parent_name,
                "last_crawled_at": cat.last_crawled_at,
            },
        })

    # 精确匹配排前面，模糊匹配按 rank 排
    items.sort(key=lambda x: (
        0 if x["brand_name"].lower() == name.lower() else 1,
        x["rank"]
    ))

    return {
        "keyword": name,
        "total": len(items),
        "items": items,
    }
