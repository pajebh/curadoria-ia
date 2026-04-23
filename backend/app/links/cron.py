from __future__ import annotations

import asyncio

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.links.validator import revalidar_itens

log = structlog.get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _job_revalidar_links() -> None:
    from app.core.db import AsyncSessionLocal
    from app.planos.repository import listar_itens_para_revalidar
    from app.planos.models import Plan, PlanCategory, PlanItem  # noqa: F401

    log.info("cron_revalidacao_iniciado")
    async with AsyncSessionLocal() as db:
        itens = await listar_itens_para_revalidar(db)

    if not itens:
        log.info("cron_revalidacao_sem_itens")
        return

    # Group items by plan tema for better search queries
    # Since we don't have tema here easily, use item nome only
    await revalidar_itens(itens, tema="")
    log.info("cron_revalidacao_concluido", total=len(itens))


def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        lambda: asyncio.ensure_future(_job_revalidar_links()),
        trigger="cron",
        day_of_week="mon",
        hour=3,
        minute=0,
        id="revalidar_links",
        replace_existing=True,
    )
    _scheduler.start()
    log.info("scheduler_iniciado")


def stop_scheduler() -> None:
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("scheduler_parado")
