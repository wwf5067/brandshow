import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category

logger = logging.getLogger(__name__)


async def upsert_categories(db: AsyncSession, categories_data: list[dict]) -> int:
    """Insert new categories or update group_name/parent_name for existing ones."""
    added = 0
    updated = 0
    for data in categories_data:
        slug = data.get("slug", "").strip()
        if not slug:
            continue
        result = await db.execute(select(Category).where(Category.slug == slug))
        existing = result.scalar_one_or_none()
        if existing:
            # Update hierarchy fields if we now have richer data
            changed = False
            if data.get("group_name") and not existing.group_name:
                existing.group_name = data["group_name"]
                changed = True
            if data.get("parent_name") and not existing.parent_name:
                existing.parent_name = data["parent_name"]
                changed = True
            if changed:
                updated += 1
        else:
            db.add(Category(
                name=data["name"],
                url=data["url"],
                slug=slug,
                group_name=data.get("group_name"),
                parent_name=data.get("parent_name"),
            ))
            added += 1

    await db.commit()
    logger.info("Categories: %d new, %d updated hierarchy", added, updated)
    return added
