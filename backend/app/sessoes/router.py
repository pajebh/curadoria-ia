from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_session, get_db_rls
from app.planos import repository as repo
from app.planos.schemas import PlanoResumo
from app.sessoes.models import Session
from app.sessoes.service import criar_sessao

router = APIRouter(prefix="/sessoes", tags=["sessoes"])

COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 180 * 24 * 60 * 60


@router.post("", status_code=201)
async def criar_sessao_endpoint(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    _session_id, token = await criar_sessao(db)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="none",
    )
    return {"message": "Sessão criada"}


@router.get("/me/planos")
async def listar_planos_sessao(
    cursor: UUID | None = None,
    session_id: UUID = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_rls),
) -> dict:
    items, next_cursor = await repo.listar_planos_sessao(db, session_id, cursor)
    return {
        "items": [PlanoResumo.model_validate(p) for p in items],
        "next_cursor": str(next_cursor) if next_cursor else None,
    }


@router.delete("/me", status_code=204)
async def deletar_sessao(
    response: Response,
    session_id: UUID = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_rls),
) -> None:
    await db.execute(delete(Session).where(Session.id == session_id))
    await db.commit()
    response.delete_cookie(COOKIE_NAME, httponly=True, samesite="strict")
