import structlog
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.planos.models import LGPDDeletion
from app.sessoes.models import Session

log = structlog.get_logger(__name__)


async def purge_sessoes_expiradas(db: AsyncSession) -> int:
    """Apaga sessões com purge_at < now() e registra em lgpd_deletions. Retorna contagem."""
    now = func.now()

    expiradas = await db.execute(
        select(Session).where(Session.purge_at < now)
    )
    sessoes = expiradas.scalars().all()

    if not sessoes:
        return 0

    count = len(sessoes)
    for sessao in sessoes:
        registro = LGPDDeletion(
            session_hash=sessao.token_hash,
            items_deleted=0,
        )
        db.add(registro)
        await db.delete(sessao)

    await db.commit()

    for registro in await db.execute(
        select(LGPDDeletion).where(LGPDDeletion.executed_at.is_(None))
    ):
        pass  # TODO: update executed_at

    log.info("lgpd_purge_completed", sessions_purged=count)
    return count
