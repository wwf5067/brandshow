from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.category import Category
from app.models.brand import Brand
from app.schemas.category import (
    CategoryResponse,
    CategoryListResponse,
    CategoryBrandsResponse,
    GroupListResponse,
    GroupResponse,
    ParentGroupResponse,
)
from app.schemas.brand import BrandResponse

router = APIRouter(prefix="/categories", tags=["categories"])


async def _with_brand_count(db: AsyncSession, cats: list[Category]) -> list[CategoryResponse]:
    """Attach brand_count to a list of Category ORM objects."""
    if not cats:
        return []
    ids = [c.id for c in cats]
    count_result = await db.execute(
        select(Brand.category_id, func.count(Brand.id).label("cnt"))
        .where(Brand.category_id.in_(ids))
        .group_by(Brand.category_id)
    )
    count_map = {row.category_id: row.cnt for row in count_result}
    items = []
    for cat in cats:
        item = CategoryResponse.model_validate(cat)
        item.brand_count = count_map.get(cat.id, 0)
        items.append(item)
    return items


@router.get("/meta")
async def get_categories_meta(db: AsyncSession = Depends(get_db)):
    """返回所有大类和中类列表，用于筛选器。"""
    groups_result = await db.execute(
        select(Category.group_name)
        .where(Category.group_name.isnot(None))
        .distinct()
        .order_by(Category.group_name)
    )
    groups = [r[0] for r in groups_result]

    parents_result = await db.execute(
        select(Category.group_name, Category.parent_name)
        .where(Category.parent_name.isnot(None))
        .distinct()
        .order_by(Category.group_name, Category.parent_name)
    )
    parents: dict[str, list[str]] = {}
    for row in parents_result:
        parents.setdefault(row[0], []).append(row[1])

    return {"groups": groups, "parents": parents}


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    search: str = Query("", description="Filter by category name"),
    group_name: str = Query("", description="Filter by group name"),
    parent_name: str = Query("", description="Filter by parent name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Category).where(Category.is_active.is_(True))
    if search:
        query = query.where(Category.name.ilike(f"%{search}%"))
    if group_name:
        query = query.where(Category.group_name == group_name)
    if parent_name:
        query = query.where(Category.parent_name == parent_name)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = query.order_by(Category.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    categories = result.scalars().all()

    items = await _with_brand_count(db, list(categories))
    return CategoryListResponse(total=total, items=items)


@router.get("/groups", response_model=GroupListResponse)
async def list_category_groups(
    search: str = Query("", description="Search across all levels"),
    db: AsyncSession = Depends(get_db),
):
    """Return 3-level tree: group → parent → category.
    When searching, return flat list under a synthetic group.
    """
    query = select(Category).where(Category.is_active.is_(True))
    if search:
        query = query.where(Category.name.ilike(f"%{search}%"))
    query = query.order_by(Category.group_name, Category.parent_name, Category.name)

    result = await db.execute(query)
    all_cats = result.scalars().all()
    items = await _with_brand_count(db, list(all_cats))

    if search:
        # 搜索时直接返回扁平列表，放在一个特殊 group 里
        return GroupListResponse(
            groups=[GroupResponse(
                group_name=f'搜索"{search}"的结果',
                total_categories=len(items),
                parents=[ParentGroupResponse(parent_name=None, categories=items)],
            )],
            ungrouped=[],
        )

    # 按 group_name → parent_name 聚合
    grouped: dict[str, dict[str | None, list[CategoryResponse]]] = defaultdict(lambda: defaultdict(list))
    ungrouped: list[CategoryResponse] = []

    for item in items:
        if item.group_name:
            grouped[item.group_name][item.parent_name].append(item)
        else:
            ungrouped.append(item)

    groups = []
    for group_name, parent_map in grouped.items():
        parents = []
        for parent_name, cats in parent_map.items():
            parents.append(ParentGroupResponse(parent_name=parent_name, categories=cats))
        # 有 parent_name 的排前面
        parents.sort(key=lambda p: (p.parent_name is None, p.parent_name or ""))
        groups.append(GroupResponse(
            group_name=group_name,
            total_categories=sum(len(p.categories) for p in parents),
            parents=parents,
        ))

    # 大类按名称排序
    groups.sort(key=lambda g: g.group_name)

    return GroupListResponse(groups=groups, ungrouped=ungrouped)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")
    items = await _with_brand_count(db, [cat])
    return items[0]


@router.get("/{category_id}/brands", response_model=CategoryBrandsResponse)
async def get_category_brands(category_id: int, db: AsyncSession = Depends(get_db)):
    cat_result = await db.execute(select(Category).where(Category.id == category_id))
    cat = cat_result.scalar_one_or_none()
    if not cat:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")

    brands_result = await db.execute(
        select(Brand).where(Brand.category_id == category_id).order_by(Brand.rank)
    )
    brands = brands_result.scalars().all()

    return CategoryBrandsResponse(
        category_id=category_id,
        category_name=cat.name,
        brands=[BrandResponse.model_validate(b) for b in brands],
    )
