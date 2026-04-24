from __future__ import annotations

import httpx
import structlog

from app.core.config import settings

log = structlog.get_logger(__name__)

_TIMEOUT = 8.0


async def buscar_youtube(query: str) -> str | None:
    """YouTube Data API v3 — returns first video URL or None.

    Costs 100 units/query. Free quota: 10.000 units/day (~100 queries).
    """
    if not settings.youtube_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": 1,
                    "relevanceLanguage": "pt",
                    "key": settings.youtube_api_key,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if items:
                video_id = items[0]["id"]["videoId"]
                return f"https://www.youtube.com/watch?v={video_id}"
    except Exception as exc:
        log.warning("youtube_api_falhou", query=query, error=str(exc))
    return None


async def buscar_wikipedia(query: str) -> str | None:
    """Wikipedia (pt) search API — returns article URL or None. Free, no key."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://pt.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": 1,
                },
            )
            resp.raise_for_status()
            results = resp.json().get("query", {}).get("search", [])
            if results:
                title = results[0]["title"].replace(" ", "_")
                return f"https://pt.wikipedia.org/wiki/{title}"
    except Exception as exc:
        log.warning("wikipedia_api_falhou", query=query, error=str(exc))
    return None


async def buscar_itunes(query: str, entity: str = "podcast") -> str | None:
    """iTunes Search API — returns first result URL or None. Free, no key.

    entity: 'podcast' | 'audiobook' | 'ebook'
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://itunes.apple.com/search",
                params={
                    "term": query,
                    "entity": entity,
                    "limit": 1,
                    "country": "BR",
                    "lang": "pt_br",
                },
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if results:
                url = results[0].get("collectionViewUrl") or results[0].get("trackViewUrl")
                if url and isinstance(url, str):
                    return url
    except Exception as exc:
        log.warning("itunes_api_falhou", query=query, error=str(exc))
    return None


async def buscar_openlibrary(query: str) -> str | None:
    """OpenLibrary search API — returns work URL or None. Free, no key."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://openlibrary.org/search.json",
                params={"q": query, "limit": 1},
            )
            resp.raise_for_status()
            docs = resp.json().get("docs", [])
            if docs:
                key = docs[0].get("key")
                if key:
                    return f"https://openlibrary.org{key}"
    except Exception as exc:
        log.warning("openlibrary_api_falhou", query=query, error=str(exc))
    return None
