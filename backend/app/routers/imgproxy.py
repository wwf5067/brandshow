"""图片代理：绕过 img.chinapp.com 防盗链，由后端转发并缓存。"""
import asyncio
import hashlib
import logging
import random
from pathlib import Path

import httpx
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from app.crawler.user_agents import UA_POOL

router = APIRouter(prefix="/img-proxy", tags=["imgproxy"])
logger = logging.getLogger(__name__)

# 内存缓存：url_hash -> (content_type, bytes)
_cache: dict[str, tuple[str, bytes]] = {}
_MAX_CACHE = 500


@router.get("/{path:path}")
async def proxy_image(path: str):
    """代理 img.chinapp.com 图片，加上正确的 Referer 绕过防盗链。"""
    url = f"https://img.chinapp.com/{path}"
    cache_key = hashlib.md5(url.encode()).hexdigest()

    if cache_key in _cache:
        ct, data = _cache[cache_key]
        return Response(content=data, media_type=ct,
                        headers={"Cache-Control": "public, max-age=604800"})

    headers = {
        "User-Agent": random.choice(UA_POOL),
        "Referer": "https://www.chinapp.com/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return Response(status_code=resp.status_code)

            ct = resp.headers.get("content-type", "image/png")
            data = resp.content

            # 简单 LRU：超限时清空一半
            if len(_cache) >= _MAX_CACHE:
                keys = list(_cache.keys())[:_MAX_CACHE // 2]
                for k in keys:
                    del _cache[k]

            _cache[cache_key] = (ct, data)
            return Response(content=data, media_type=ct,
                            headers={"Cache-Control": "public, max-age=604800"})
    except Exception as e:
        logger.warning("img-proxy error for %s: %s", url, e)
        return Response(status_code=502)
