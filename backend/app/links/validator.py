from __future__ import annotations

import asyncio
from urllib.parse import urlparse
from uuid import UUID

import httpx
import structlog

from app.core.config import settings
from app.links.google_search import buscar_url_substituta
from app.planos.models import LinkStatus, PlanItem
from app.planos.sse import sse_manager

log = structlog.get_logger(__name__)

_HEAD_TIMEOUT = 5.0
_MAX_REDIRECTS = 3
_CONCURRENCY = 5  # simultaneous HEAD requests per plan


async def _head_ok(url: str) -> bool:
    """Return True if URL responds with 2xx or 3xx within timeout."""
    try:
        async with httpx.AsyncClient(
            timeout=_HEAD_TIMEOUT,
            follow_redirects=True,
            max_redirects=_MAX_REDIRECTS,
        ) as client:
            resp = await client.head(url)
            return resp.status_code < 400
    except Exception:
        return False


async def _validar_item(
    item: PlanItem,
    tema: str,
    cse_key: str,
    sem: asyncio.Semaphore,
    cse_id: str = "",
) -> tuple[UUID, LinkStatus, str | None]:
    """Validate one item. Returns (item_id, new_status, new_link_or_None)."""
    async with sem:
        ok = await _head_ok(item.link)
        if ok:
            return item.id, LinkStatus.valid, None

        # HEAD failed — try Google CSE repair
        if cse_key and cse_id:
            dominio = urlparse(item.link).netloc or None
            novo_link = await buscar_url_substituta(
                cse_key, cse_id, item.nome, tema, dominio
            )
            if novo_link:
                log.info(
                    "link_reparado",
                    item_id=str(item.id),
                    original=item.link,
                    novo=novo_link,
                )
                return item.id, LinkStatus.repaired, novo_link

        log.warning("link_quebrado", item_id=str(item.id), url=item.link)
        return item.id, LinkStatus.broken, None


async def validar_e_reparar_plano(plan_id: UUID, tema: str) -> None:
    """Background task: validate all items of a plan and publish SSE link_check events."""
    from app.core.db import AsyncSessionLocal
    from app.planos.repository import atualizar_link_item, listar_itens_plano

    cse_key = settings.google_cse_key
    cse_id = settings.google_cse_id
    sem = asyncio.Semaphore(_CONCURRENCY)

    async with AsyncSessionLocal() as db:
        itens = await listar_itens_plano(db, plan_id)

    if not itens:
        sse_manager.publish(str(plan_id), {"event": "complete"})
        return

    tasks = [
        _validar_item(item, tema, cse_key, sem, cse_id)
        for item in itens
    ]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)

    async with AsyncSessionLocal() as db:
        for resultado in resultados:
            if isinstance(resultado, Exception):
                log.error("validar_item_erro", error=str(resultado))
                continue
            item_id, status, novo_link = resultado
            await atualizar_link_item(db, item_id, status, novo_link)
            payload: dict = {
                "event": "link_check",
                "item_id": str(item_id),
                "status": status.value,
            }
            if novo_link:
                payload["link"] = novo_link
            sse_manager.publish(str(plan_id), payload)

    sse_manager.publish(str(plan_id), {"event": "complete"})
    log.info("validacao_concluida", plan_id=str(plan_id), total=len(itens))


async def revalidar_itens(itens: list[PlanItem], tema: str) -> None:
    """Re-validate a list of items (used by weekly cron). No SSE — updates DB directly."""
    from app.core.db import AsyncSessionLocal
    from app.planos.repository import atualizar_link_item

    cse_key = settings.google_cse_key
    cse_id = settings.google_cse_id
    sem = asyncio.Semaphore(_CONCURRENCY)

    tasks = [_validar_item(item, tema, cse_key, sem, cse_id) for item in itens]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)

    async with AsyncSessionLocal() as db:
        for resultado in resultados:
            if isinstance(resultado, Exception):
                log.error("revalidar_item_erro", error=str(resultado))
                continue
            item_id, status, novo_link = resultado
            await atualizar_link_item(db, item_id, status, novo_link)

    log.info("revalidacao_concluida", total=len(itens))
