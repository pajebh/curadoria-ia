from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_session_token, hash_token
from app.sessoes.models import Session


async def criar_sessao(db: AsyncSession) -> tuple[UUID, str]:
    session_id = uuid4()
    token = create_session_token(session_id)
    session = Session(id=session_id, token_hash=hash_token(token))
    db.add(session)
    await db.commit()
    return session_id, token


async def obter_sessao_por_hash(db: AsyncSession, token_hash: str) -> Session | None:
    result = await db.execute(select(Session).where(Session.token_hash == token_hash))
    return result.scalar_one_or_none()


async def atualizar_last_seen(db: AsyncSession, session_id: UUID) -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(last_seen_at=now)
    )
    await db.commit()
