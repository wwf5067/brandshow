import asyncio
import logging
import random
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

# Track crawler state for status API
crawler_state: dict = {
    "is_running": False,
    "last_discovery_at": None,
    "crawled_today": 0,
}


async def weekly_schedule_distributor() -> None:
    """Run every Sunday 00:01: randomly distribute all categories across the coming week."""
    from app.models.category import Category

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Category).where(Category.is_active.is_(True)))
        categories = result.scalars().all()

        random.shuffle(categories)

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # Monday

        for i, cat in enumerate(categories):
            day_offset = i % 7
            target_date = week_start + timedelta(days=day_offset)
            random_hour = random.randint(2, 22)
            random_minute = random.randint(0, 59)
            next_crawl = datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                random_hour,
                random_minute,
            )
            await db.execute(
                update(Category).where(Category.id == cat.id).values(next_crawl_at=next_crawl)
            )

        await db.commit()
        logger.info("Weekly schedule distributed for %d categories", len(categories))


async def daily_crawler_executor() -> None:
    """Run every day at 02:00: crawl categories scheduled for today."""
    from app.models.category import Category
    from app.crawler.fetcher import fetch_page
    from app.crawler.parser import parse_brand_list
    from app.services.brand_service import upsert_brands

    crawler_state["crawled_today"] = 0
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Category).where(
                Category.next_crawl_at >= today_start,
                Category.next_crawl_at < today_end,
                Category.is_active.is_(True),
            )
        )
        today_categories = result.scalars().all()
        logger.info("Daily executor: %d categories to crawl today", len(today_categories))

        for cat in today_categories:
            if cat.next_crawl_at:
                wait_seconds = (cat.next_crawl_at - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    logger.debug("Waiting %.0fs before crawling %s", wait_seconds, cat.name)
                    await asyncio.sleep(wait_seconds)

            logger.info("Crawling category: %s (%s)", cat.name, cat.url)
            html = await fetch_page(cat.url)
            if html:
                brands_data, meta = parse_brand_list(html)
                if brands_data:
                    await upsert_brands(db, cat.id, brands_data)
                    cat.last_crawled_at = datetime.now()
                    # 回写面包屑 meta
                    if meta.get("group_name") and not cat.group_name:
                        cat.group_name = meta["group_name"]
                    if meta.get("parent_name") and not cat.parent_name:
                        cat.parent_name = meta["parent_name"]
                    await db.commit()
                    crawler_state["crawled_today"] += 1
                    logger.info("Crawled %s: %d brands", cat.name, len(brands_data))
                else:
                    logger.warning("No brands parsed for %s", cat.name)
            else:
                logger.error("Failed to fetch %s", cat.url)

            # Random pause between categories: 5~15 seconds
            await asyncio.sleep(random.uniform(5, 15))


async def discover_and_crawl_all() -> int:
    """One-shot: parse 3-level category tree from /paihang/ index."""
    from app.crawler.fetcher import fetch_page
    from app.crawler.parser import parse_category_tree
    from app.services.category_service import upsert_categories

    html = await fetch_page("https://www.chinapp.com/paihang/")
    if not html:
        logger.error("Failed to fetch /paihang/ index")
        return 0

    cats = parse_category_tree(html)
    async with AsyncSessionLocal() as db:
        added = await upsert_categories(db, cats)

    crawler_state["last_discovery_at"] = datetime.now().isoformat()
    logger.info("Discovery complete: %d new/updated categories", added)
    return added


def setup_scheduler() -> None:
    scheduler.add_job(
        weekly_schedule_distributor,
        "cron",
        day_of_week="sun",
        hour=0,
        minute=1,
        id="weekly_distributor",
        replace_existing=True,
    )
    scheduler.add_job(
        daily_crawler_executor,
        "cron",
        hour=2,
        minute=0,
        id="daily_executor",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")
