import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.category import Category
from app.models.brand import Brand
from app.schemas.category import CrawlerStatusResponse

router = APIRouter(prefix="/crawler", tags=["crawler"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=CrawlerStatusResponse)
async def crawler_status(db: AsyncSession = Depends(get_db)):
    from app.crawler.scheduler import crawler_state

    total_cats = (await db.execute(select(func.count(Category.id)))).scalar_one()
    active_cats = (
        await db.execute(select(func.count(Category.id)).where(Category.is_active.is_(True)))
    ).scalar_one()
    total_brands = (await db.execute(select(func.count(Brand.id)))).scalar_one()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    crawled_today = (
        await db.execute(
            select(func.count(Category.id)).where(
                Category.last_crawled_at >= today_start,
                Category.last_crawled_at < today_end,
            )
        )
    ).scalar_one()

    pending_today = (
        await db.execute(
            select(func.count(Category.id)).where(
                Category.next_crawl_at >= today_start,
                Category.next_crawl_at < today_end,
                Category.last_crawled_at == None,  # noqa: E711
            )
        )
    ).scalar_one()

    total_groups = (
        await db.execute(
            select(func.count(func.distinct(Category.group_name))).where(
                Category.group_name.isnot(None)
            )
        )
    ).scalar_one()

    total_parents = (
        await db.execute(
            select(func.count(func.distinct(Category.parent_name))).where(
                Category.parent_name.isnot(None)
            )
        )
    ).scalar_one()

    return CrawlerStatusResponse(
        total_categories=total_cats,
        active_categories=active_cats,
        total_groups=total_groups,
        total_parents=total_parents,
        crawled_today=crawled_today,
        pending_today=pending_today,
        total_brands=total_brands,
        last_discovery_at=crawler_state.get("last_discovery_at"),
        is_running=crawler_state.get("is_running", False),
    )


@router.post("/discover")
async def trigger_discover(background_tasks: BackgroundTasks):
    """Manually trigger category discovery."""
    from app.crawler.scheduler import discover_and_crawl_all, crawler_state

    if crawler_state.get("is_running"):
        raise HTTPException(status_code=409, detail="Crawler is already running")

    async def run():
        crawler_state["is_running"] = True
        try:
            added = await discover_and_crawl_all()
            logger.info("Discovery complete: %d new categories", added)
        finally:
            crawler_state["is_running"] = False

    background_tasks.add_task(run)
    return {"message": "Category discovery started in background"}


@router.post("/trigger/{category_id}")
async def trigger_category(category_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Manually trigger crawl for a single category."""
    from app.crawler.fetcher import fetch_page
    from app.crawler.parser import parse_brand_list
    from app.services.brand_service import upsert_brands

    cat_result = await db.execute(select(Category).where(Category.id == category_id))
    cat = cat_result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    async def run():
        from app.database import AsyncSessionLocal
        html = await fetch_page(cat.url)
        if html:
            brands_data, meta = parse_brand_list(html)
            async with AsyncSessionLocal() as session:
                if brands_data:
                    await upsert_brands(session, category_id, brands_data)
                cat_row = (await session.execute(select(Category).where(Category.id == category_id))).scalar_one()
                cat_row.last_crawled_at = datetime.now()
                if meta.get("group_name") and not cat_row.group_name:
                    cat_row.group_name = meta["group_name"]
                if meta.get("parent_name") and not cat_row.parent_name:
                    cat_row.parent_name = meta["parent_name"]
                await session.commit()

    background_tasks.add_task(run)
    return {"message": f"Crawl triggered for category '{cat.name}'"}


@router.post("/schedule/weekly")
async def trigger_weekly_schedule():
    """Manually trigger weekly schedule distribution."""
    from app.crawler.scheduler import weekly_schedule_distributor
    background_tasks = BackgroundTasks()
    background_tasks.add_task(weekly_schedule_distributor)
    asyncio.create_task(weekly_schedule_distributor())
    return {"message": "Weekly schedule distribution triggered"}
