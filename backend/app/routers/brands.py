from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, cast, distinct
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brand import Brand
from app.models.brand_rank_history import BrandRankHistory
from app.models.category import Category
from app.schemas.brand import RankHistoryItem, TaggedBrandItem

router = APIRouter(prefix="/brands", tags=["brands"])


# ── 品牌反查 ──────────────────────────────────────────────────────────────────

@router.get("/search")
async def search_brands(
    name: str = Query(..., min_length=1, description="品牌名关键词"),
    db: AsyncSession = Depends(get_db),
):
    """输入品牌名，返回该品牌出现在哪些类别的 Top10 排行榜中，附带情报聚合字段。"""
    result = await db.execute(
        select(Brand, Category)
        .join(Category, Brand.category_id == Category.id)
        .where(Brand.name.ilike(f"%{name}%"))
        .order_by(Brand.rank)
    )
    rows = result.all()

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
            "tags": brand.tags,
            "brand_note": brand.brand_note,
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

    # 品牌情报聚合字段
    top_rank = min((i["rank"] for i in items), default=None)
    groups = list(dict.fromkeys(
        i["category"]["group_name"] for i in items
        if i["category"]["group_name"]
    ))

    return {
        "keyword": name,
        "total": len(items),
        "top_rank": top_rank,
        "group_count": len(groups),
        "groups": groups,
        "items": items,
    }


# ── 排名历史 ──────────────────────────────────────────────────────────────────

@router.get("/{brand_id}/rank-history", response_model=list[RankHistoryItem])
async def get_rank_history(
    brand_id: int,
    limit: int = Query(12, ge=1, le=52, description="返回最近几条记录"),
    db: AsyncSession = Depends(get_db),
):
    """返回某品牌在其所属品类的排名历史（最近 N 次爬取快照，按时间升序）。"""
    # 先验证品牌存在
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    result = await db.execute(
        select(BrandRankHistory)
        .where(
            BrandRankHistory.brand_id == brand_id,
            BrandRankHistory.category_id == brand.category_id,
        )
        .order_by(BrandRankHistory.recorded_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    # 返回升序（从旧到新，方便前端画趋势线）
    return list(reversed(history))


# ── 标签品牌通用查询（避雷 / 国货）────────────────────────────────────────────

async def _get_tagged_brands(
    db: AsyncSession,
    tag: str,
    group_name: str | None,
    page: int,
    page_size: int,
) -> dict:
    """查询含指定标签的品牌列表，支持按大类筛选和分页。"""
    base = (
        select(Brand, Category)
        .join(Category, Brand.category_id == Category.id)
        .where(cast(Brand.tags, JSONB).contains([tag]))
    )
    if group_name:
        base = base.where(Category.group_name == group_name)

    # 总数（复用同一查询条件）
    count_q = (
        select(Brand.id)
        .join(Category, Brand.category_id == Category.id)
        .where(cast(Brand.tags, JSONB).contains([tag]))
    )
    if group_name:
        count_q = count_q.where(Category.group_name == group_name)
    total = len((await db.execute(count_q)).all())

    rows = (await db.execute(
        base
        .order_by(Category.group_name, Category.name, Brand.rank)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all()

    items = [
        TaggedBrandItem(
            brand_id=brand.id,
            name=brand.name,
            rank=brand.rank,
            logo_url=brand.logo_url,
            tags=brand.tags,
            brand_note=brand.brand_note,
            category={"id": cat.id, "name": cat.name,
                      "group_name": cat.group_name, "parent_name": cat.parent_name},
        )
        for brand, cat in rows
    ]

    # 全量大类列表（不受分页和 group_name 过滤影响，用于前端筛选栏）
    groups_result = await db.execute(
        select(distinct(Category.group_name))
        .join(Brand, Brand.category_id == Category.id)
        .where(cast(Brand.tags, JSONB).contains([tag]))
        .where(Category.group_name.isnot(None))
        .order_by(Category.group_name)
    )
    all_groups = [r[0] for r in groups_result.all()]

    return {"total": total, "page": page, "page_size": page_size, "items": items, "groups": all_groups}


@router.get("/blacklist")
async def get_blacklist(
    group_name: str | None = Query(None, description="按大类筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """避雷榜：返回所有标注了「避雷」标签的品牌。"""
    return await _get_tagged_brands(db, "避雷", group_name, page, page_size)


@router.get("/domestic")
async def get_domestic(
    group_name: str | None = Query(None, description="按大类筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """国货专区：返回所有标注了「国货之光」标签的品牌。"""
    return await _get_tagged_brands(db, "国货之光", group_name, page, page_size)
