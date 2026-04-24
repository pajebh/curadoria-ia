from __future__ import annotations

import asyncio
from uuid import UUID

import httpx
import structlog

from app.links.repair import gerar_url_busca
from app.planos.models import LinkStatus, PlanItem
from app.planos.sse import sse_manager

log = structlog.get_logger(__name__)

_HEAD_TIMEOUT = 5.0
_MAX_REDIRECTS = 3
_CONCURRENCY = 5


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
    sem: asyncio.Semaphore,
) -> tuple[UUID, LinkStatus, str | None]:
    """Validate one item. Returns (item_id, new_status, new_link_or_None)."""
    async with sem:
        if await _head_ok(item.link):
            return item.id, LinkStatus.valid, None

        # HEAD failed — build a deterministic search URL (always valid)
        categoria_nome = item.categoria.nome.value
        novo_link = gerar_url_busca(item.nome, tema, categoria_nome)
        log.info(
            "link_substituido_por_busca",
            item_id=str(item.id),
            original=item.link,
            busca=novo_link,
        )
        return item.id, LinkStatus.repaired, novo_link


async def validar_e_reparar_plano(plan_id: UUID, tema: str) -> None:
    """Background task: validate all items of a plan and publish SSE link_check events."""
    from app.core.db import AsyncSessionLocal
    from app.planos.repository import atualizar_link_item, listar_itens_plano

    sem = asyncio.Semaphore(_CONCURRENCY)

    async with AsyncSessionLocal() as db:
        itens = await listar_itens_plano(db, plan_id)

    if not itens:
        sse_manager.publish(str(plan_id), {"event": "complete"})
        return

    tasks = [_validar_item(item, tema, sem) for item in itens]
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
    """Re-validate items (used by weekly cron). No SSE — updates DB directly."""
    from app.core.db import AsyncSessionLocal
    from app.planos.repository import atualizar_link_item

    sem = asyncio.Semaphore(_CONCURRENCY)
    tasks = [_validar_item(item, tema, sem) for item in itens]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)

    async with AsyncSessionLocal() as db:
        for resultado in resultados:
            if isinstance(resultado, Exception):
                log.error("revalidar_item_erro", error=str(resultado))
                continue
            item_id, status, novo_link = resultado
            await atualizar_link_item(db, item_id, status, novo_link)

    log.info("revalidacao_concluida", total=len(itens))
