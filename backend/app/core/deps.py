from collections.abc import AsyncGenerator
from uuid import UUID

import sqlalchemy
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import decode_session_token, hash_token
from app.sessoes.service import atualizar_last_seen, obter_sessao_por_hash


async def get_current_session(request: Request) -> UUID:
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Sessão não encontrada")
    session_id = decode_session_token(token)
    if not session_id:
        raise HTTPException(status_code=401, detail="Token inválido")
    async with AsyncSessionLocal() as db:
        sessao = await obter_sessao_por_hash(db, hash_token(token))
        if not sessao:
            raise HTTPException(status_code=401, detail="Sessão inválida")
        await atualizar_last_seen(db, session_id)
    return session_id


async def get_db_rls(
    session_id: UUID = Depends(get_current_session),
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        await session.execute(
            sqlalchemy.text(f"SET LOCAL app.session_id = '{session_id}'")
        )
        yield session
