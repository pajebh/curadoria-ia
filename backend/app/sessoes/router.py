from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.sessoes.service import criar_sessao

router = APIRouter(prefix="/sessoes", tags=["sessoes"])

COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 180 * 24 * 60 * 60  # 180 dias em segundos


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
        samesite="strict",
    )
    return {"message": "Sessão criada"}
