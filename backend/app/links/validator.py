from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from typing import Any
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

_SEPARADORES_DESCRITIVOS = (" — ", " – ", " - ", ": ")
_PARENTESES_RE = re.compile(r"\([^)]*\)")


def _limpar_nome(nome: str) -> str:
    """Remove caudas descritivas (após traço/dois-pontos) e parentéticos.

    APIs de busca (iTunes, Wikipedia, OpenLibrary) retornam 0 resultados quando
    a query é muito específica (ex.: "Curso Beach Tennis Brasil — fundamentos").
    """
    for sep in _SEPARADORES_DESCRITIVOS:
        if sep in nome:
            nome = nome.split(sep, 1)[0]
            break
    nome = _PARENTESES_RE.sub("", nome)
    return " ".join(nome.split()).strip()


async def _buscar_com_fallback(
    fn: Callable[..., Awaitable[str | None]],
    queries: list[str],
    **kwargs: Any,
) -> str | None:
    for q in queries:
        if not q:
            continue
        resultado = await fn(q, **kwargs)
        if resultado:
            return resultado
    return None


async def _enriquecer_item(
    item: PlanItem,
    tema: str,
    sem: asyncio.Semaphore,
) -> tuple[UUID, LinkStatus, str | None]:
    """Fetch a real URL for the item via the category-appropriate search API.

    Tenta primeiro com o nome limpo do item; se falhar, tenta só com o tema;
    se ainda falhar, cai num URL de busca (Google/Spotify/YouTube) por categoria.
    """
    async with sem:
        categoria = item.categoria.nome.value
        nome_limpo = _limpar_nome(item.nome)
        # Dedup: se o nome limpo já contém o tema, não repete
        if tema.lower() in nome_limpo.lower():
            queries = [nome_limpo, tema]
        else:
            queries = [f"{nome_limpo} {tema}".strip(), nome_limpo, tema]

        novo_link: str | None = None

        if categoria in ("formal", "visual"):
            novo_link = await _buscar_com_fallback(buscar_youtube, queries)
        elif categoria == "audio":
            novo_link = await _buscar_com_fallback(
                buscar_itunes, queries, entity="podcast"
            )
        elif categoria == "leitura":
            novo_link = await _buscar_com_fallback(buscar_openlibrary, queries)
            if not novo_link:
                novo_link = await _buscar_com_fallback(buscar_wikipedia, queries)
        elif categoria == "referencias":
            novo_link = await _buscar_com_fallback(buscar_wikipedia, queries)

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
