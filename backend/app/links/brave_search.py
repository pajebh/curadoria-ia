from __future__ import annotations

import structlog
import httpx

log = structlog.get_logger(__name__)

_BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
_TIMEOUT = 8.0


async def buscar_url_substituta(
    api_key: str,
    nome_item: str,
    tema: str,
    dominio_original: str | None = None,
) -> str | None:
    """Return the first Brave Search result URL for the given item, or None on failure."""
    query = f'"{nome_item}" {tema}'
    if dominio_original:
        query += f" site:{dominio_original}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                _BRAVE_URL,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": api_key,
                },
                params={"q": query, "count": 1, "search_lang": "pt"},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("web", {}).get("results", [])
            if results:
                url: str = results[0]["url"]
                return url
    except Exception as exc:
        log.warning("brave_search_falhou", query=query, error=str(exc))

    return None
