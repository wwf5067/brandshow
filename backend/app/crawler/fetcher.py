import asyncio
import logging
import random

import httpx

from app.crawler.user_agents import UA_POOL

logger = logging.getLogger(__name__)

# Only use desktop UAs to avoid mobile redirect
DESKTOP_UAS = [ua for ua in UA_POOL if "Mobile" not in ua and "iPhone" not in ua and "iPad" not in ua]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}


async def fetch_page(url: str, retries: int = 3) -> str | None:
    ua = random.choice(DESKTOP_UAS)
    headers = {**BASE_HEADERS, "User-Agent": ua}
    if "/paihang/" in url:
        headers["Referer"] = "https://www.chinapp.com/paihang/"

    for attempt in range(retries):
        await asyncio.sleep(random.uniform(2, 8))
        try:
            async with httpx.AsyncClient(
                timeout=30,
                follow_redirects=True,
                headers=headers,
            ) as client:
                resp = await client.get(url)

                # Reject redirect to mobile site
                if "m.chinapp.com" in str(resp.url):
                    logger.warning("Redirected to mobile site for %s, retrying with www (attempt %d/%d)", url, attempt + 1, retries)
                    await asyncio.sleep(random.uniform(5, 15))
                    continue

                # Reject redirect to 403/error page
                if "403" in str(resp.url) or "/error/" in str(resp.url):
                    logger.warning("Got 403 error page for %s (attempt %d/%d)", url, attempt + 1, retries)
                    await asyncio.sleep(random.uniform(15, 30))
                    continue

                resp.raise_for_status()
                return resp.text

        except httpx.HTTPStatusError as e:
            logger.warning("HTTP %s fetching %s (attempt %d/%d)", e.response.status_code, url, attempt + 1, retries)
            if e.response.status_code in (403, 429, 503):
                await asyncio.sleep((2 ** attempt) * random.uniform(10, 20))
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPError) as e:
            logger.warning("Request error fetching %s: %s (attempt %d/%d)", url, e, attempt + 1, retries)
            if attempt < retries - 1:
                await asyncio.sleep(random.uniform(10, 30))

    logger.error("Failed to fetch %s after %d attempts", url, retries)
    return None
