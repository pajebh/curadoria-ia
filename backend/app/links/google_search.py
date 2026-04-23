from __future__ import annotations

import httpx
import structlog

log = structlog.get_logger(__name__)

_GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"
_TIMEOUT = 8.0


async def buscar_url_substituta(
    api_key: str,
    cx: str,
    nome_item: str,
    tema: str,
    dominio_original: str | None = None,
) -> str | None:
    """Return the first Google CSE result URL for the item, or None on failure.

    Free tier: 100 queries/day (~3,000/month). Only called when HEAD check fails.
    """
    query = f"{nome_item} {tema}"
    if dominio_original:
        query += f" site:{dominio_original}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                _GOOGLE_CSE_URL,
                params={
                    "key": api_key,
                    "cx": cx,
                    "q": query,
                    "num": 1,
                    "lr": "lang_pt",
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if items:
                url: str = items[0]["link"]
                return url
    except Exception as exc:
        log.warning("google_cse_falhou", query=query, error=str(exc))

    return None
