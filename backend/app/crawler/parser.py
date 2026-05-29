import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.chinapp.com"

PODIUM_RANK = {
    "rank_top2_box": 1,
    "rank_top1_box": 2,
    "rank_top3_box": 3,
}


def parse_brand_list(html: str) -> tuple[list[dict], dict]:
    """Parse top-10 brands and category meta from a /paihang/{slug} page.

    Returns (brands, meta) where meta = {"group_name": str|None, "parent_name": str|None}
    """
    soup = BeautifulSoup(html, "lxml")
    brands: list[dict] = []

    # ── breadcrumb meta ────────────────────────────────────────────────────
    meta = {"group_name": None, "parent_name": None}
    crumb_items = [
        a.get_text(strip=True)
        for a in soup.select("ul.rank_crumbs_bar a")
        if a.get_text(strip=True) not in ("首页", "品牌排行")
    ]
    if len(crumb_items) >= 1:
        meta["group_name"] = crumb_items[0]
    if len(crumb_items) >= 2:
        meta["parent_name"] = crumb_items[1]

    # ── Top 3 (podium) ─────────────────────────────────────────────────────
    main_top3 = soup.find(
        "div",
        class_=lambda c: c and "rank_top_three_box" in c.split()
        and "hot_rank_top3" not in c.split(),
    )

    for css_class, rank in PODIUM_RANK.items():
        box = (main_top3.find("div", class_=css_class) if main_top3 else None) \
              or soup.find("div", class_=css_class)
        if not box:
            continue
        name_el = box.find("h3")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        if not name:
            continue

        logo_url = None
        img = box.find("img", class_="top_company_name")
        if img:
            src = img.get("data-src") or img.get("src", "")
            logo_url = ("https:" + src) if src.startswith("//") else src or None

        detail_url = None
        a = box.find("a", href=re.compile(r"/pinpai/\d+"))
        if a:
            href = a["href"]
            detail_url = (BASE_URL + href) if href.startswith("/") else href

        brands.append({
            "rank": rank, "name": name, "brand_index": None, "likes": None,
            "logo_url": logo_url, "detail_url": detail_url, "company_name": None,
        })

    # ── Rank 4-10 ──────────────────────────────────────────────────────────
    last_list = soup.find("div", class_="rank_last_list")
    if last_list:
        for li in last_list.find_all("li"):
            serial = li.find("p", class_="serial_num")
            if not serial:
                continue
            span = serial.find("span")
            if not span:
                continue
            try:
                rank = int(span.get_text(strip=True))
            except ValueError:
                continue
            if rank > 10:
                continue

            middle = li.find("div", class_="list_middle_box")
            if not middle:
                continue
            name_el = middle.find("h3")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            corp_el = middle.find("p", class_="corporate_name")
            company_name = corp_el.get_text(strip=True) if corp_el else None

            logo_url = None
            logo_a = li.find("a", class_="company_logo")
            if logo_a:
                img = logo_a.find("img")
                if img:
                    src = img.get("data-src") or img.get("src", "")
                    logo_url = ("https:" + src) if src.startswith("//") else src or None

            detail_url = None
            a = middle.find("a", href=re.compile(r"/pinpai/\d+"))
            if a:
                href = a["href"]
                detail_url = (BASE_URL + href) if href.startswith("/") else href

            brands.append({
                "rank": rank, "name": name, "brand_index": None, "likes": None,
                "logo_url": logo_url, "detail_url": detail_url,
                "company_name": company_name,
            })

    seen: set[int] = set()
    result = []
    for b in sorted(brands, key=lambda x: x["rank"]):
        if b["rank"] not in seen and b["rank"] <= 10:
            seen.add(b["rank"])
            result.append(b)

    if not result:
        logger.warning("No brands parsed from page")
    else:
        logger.info("Parsed %d brands", len(result))

    return result, meta


def parse_category_tree(html: str) -> list[dict]:
    """从 /paihang/ 首页解析完整三层分类树。

    HTML 结构:
        div.TTclas_con
          div.TTclas_tit > a  → 大类名（group_name）
          table > tr
            td > div.TTclas_ims_tit > a  → 中类名（parent_name）
            td > ul.TTclas_ims_list > li > a  → 小类链接

    Returns list of {"slug", "url", "name", "group_name", "parent_name"}
    """
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    categories: list[dict] = []

    for con in soup.select("div.TTclas"):
        tit = con.select_one("div.TTclas_tit a") or con.select_one("div.TTclas_tit")
        group_name = tit.get_text(strip=True) if tit else None

        # 大类自身链接（TTclas_tit > a）
        tit_a = con.select_one("div.TTclas_tit a")
        if tit_a:
            m = re.match(r"^(?:https?://www\.chinapp\.com)?/paihang/([^/?#]+)/?$", tit_a.get("href", ""))
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                categories.append({
                    "slug": m.group(1),
                    "url": f"https://www.chinapp.com/paihang/{m.group(1)}",
                    "name": group_name,
                    "group_name": group_name,
                    "parent_name": None,
                })

        for tr in con.select("tr"):
            # 中类自身链接（TTclas_ims_tit > a）
            parent_name = None
            parent_div = tr.find("div", class_="TTclas_ims_tit")
            if parent_div:
                a = parent_div.find("a")
                if a:
                    parent_name = a.get_text(strip=True)
                    m = re.match(r"^(?:https?://www\.chinapp\.com)?/paihang/([^/?#]+)/?$", a.get("href", ""))
                    if m and m.group(1) not in seen:
                        seen.add(m.group(1))
                        categories.append({
                            "slug": m.group(1),
                            "url": f"https://www.chinapp.com/paihang/{m.group(1)}",
                            "name": parent_name,
                            "group_name": group_name,
                            "parent_name": parent_name,
                        })

            for ul in tr.select("ul.TTclas_ims_list"):
                for a in ul.find_all("a", href=True):
                    m = re.match(
                        r"^(?:https?://www\.chinapp\.com)?/paihang/([^/?#]+)/?$",
                        a["href"],
                    )
                    if not m:
                        continue
                    slug = m.group(1)
                    if slug in seen:
                        continue
                    seen.add(slug)
                    name = a.get_text(strip=True)
                    if not name:
                        continue
                    categories.append({
                        "slug": slug,
                        "url": f"https://www.chinapp.com/paihang/{slug}",
                        "name": name,
                        "group_name": group_name,
                        "parent_name": parent_name,
                    })

    logger.info("Parsed %d categories (3-level tree) from index", len(categories))
    return categories


def parse_related_categories(html: str) -> list[dict]:
    """从品牌页「相关行业榜单」提取额外类别链接（无层级信息）。"""
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    categories: list[dict] = []

    for a in soup.select("ul.related_brand_btn a, div.related_brand a"):
        m = re.match(
            r"^(?:https?://www\.chinapp\.com)?/paihang/([^/?#]+)/?$",
            a.get("href", ""),
        )
        if not m:
            continue
        slug = m.group(1)
        if slug in seen:
            continue
        seen.add(slug)
        name = a.get_text(strip=True).replace("品牌排行榜", "").strip()
        if not name:
            continue
        categories.append({
            "slug": slug,
            "url": f"https://www.chinapp.com/paihang/{slug}",
            "name": name,
            "group_name": None,
            "parent_name": None,
        })

    return categories
