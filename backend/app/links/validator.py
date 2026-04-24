from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from app.links.enrichers import (
    buscar_itunes,
    buscar_openlibrary,
    buscar_wikipedia,
    buscar_youtube,
)
from app.links.repair import gerar_url_busca
from app.planos.models import LinkStatus, PlanItem
from app.planos.sse import sse_manager

log = structlog.get_logger(__name__)

_CONCURRENCY = 5


async def _enriquecer_item(
    item: PlanItem,
    tema: str,
    sem: asyncio.Semaphore,
) -> tuple[UUID, LinkStatus, str | None]:
    """Fetch a real URL for the item via the category-appropriate search API.
    Falls back to a Google search URL if the specific API yields no result.
    """
    async with sem:
        categoria = item.categoria.nome.value
        query = f"{item.nome} {tema}".strip()
        novo_link: str | None = None

        if categoria in ("formal", "visual"):
            novo_link = await buscar_youtube(query)
        elif categoria == "audio":
            novo_link = await buscar_itunes(query, entity="podcast")
        elif categoria == "leitura":
            novo_link = await buscar_openlibrary(query) or await buscar_wikipedia(query)
        elif categoria == "referencias":
            novo_link = await buscar_wikipedia(query)

        if not novo_link:
            novo_link = gerar_url_busca(item.nome, tema, categoria)

        if novo_link == item.link:
            return item.id, LinkStatus.valid, None

        log.info(
            "link_enriquecido",
            item_id=str(item.id),
            categoria=categoria,
            novo=novo_link,
        )
        return item.id, LinkStatus.repaired, novo_link


async def validar_e_reparar_plano(plan_id: UUID, tema: str) -> None:
    """Background task: replace AI-generated links with real URLs from search APIs."""
    from app.core.db import AsyncSessionLocal
    from app.planos.repository import atualizar_link_item, listar_itens_plano

    sem = asyncio.Semaphore(_CONCURRENCY)

    async with AsyncSessionLocal() as db:
        itens = await listar_itens_plano(db, plan_id)

    if not itens:
        sse_manager.publish(str(plan_id), {"event": "complete"})
        return

    tasks = [_enriquecer_item(item, tema, sem) for item in itens]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)

    async with AsyncSessionLocal() as db:
        for resultado in resultados:
            if isinstance(resultado, Exception):
                log.error("enriquecer_item_erro", error=str(resultado))
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
    log.info("enriquecimento_concluido", plan_id=str(plan_id), total=len(itens))


async def revalidar_itens(itens: list[PlanItem], tema: str) -> None:
    """Re-enrich items (used by weekly cron). No SSE — updates DB directly."""
    from app.core.db import AsyncSessionLocal
    from app.planos.repository import atualizar_link_item

    sem = asyncio.Semaphore(_CONCURRENCY)
    tasks = [_enriquecer_item(item, tema, sem) for item in itens]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)

    async with AsyncSessionLocal() as db:
        for resultado in resultados:
            if isinstance(resultado, Exception):
                log.error("reenriquecer_item_erro", error=str(resultado))
                continue
            item_id, status, novo_link = resultado
            await atualizar_link_item(db, item_id, status, novo_link)

    log.info("reenriquecimento_concluido", total=len(itens))
