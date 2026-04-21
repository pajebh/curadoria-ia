from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.planos.schemas import ItemPatch, PlanoAccepted, PlanoCreate, PlanoOut

router = APIRouter(prefix="/planos", tags=["planos"])


def _get_session_id() -> UUID:
    # TODO: extrair do cookie JWT via middleware
    raise HTTPException(status_code=401, detail="Sessão inválida")


@router.post("", status_code=202, response_model=PlanoAccepted)
async def criar_plano(
    body: PlanoCreate,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> PlanoAccepted:
    # TODO: implementar em módulo planos
    raise HTTPException(status_code=501, detail="Não implementado")


@router.get("/{plano_id}", response_model=PlanoOut)
async def obter_plano(
    plano_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PlanoOut:
    raise HTTPException(status_code=501, detail="Não implementado")


@router.delete("/{plano_id}", status_code=204)
async def apagar_plano(
    plano_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    raise HTTPException(status_code=501, detail="Não implementado")


@router.get("/{plano_id}/stream")
async def stream_plano(plano_id: UUID) -> StreamingResponse:
    raise HTTPException(status_code=501, detail="Não implementado")


@router.patch("/{plano_id}/itens/{item_id}")
async def patch_item(
    plano_id: UUID,
    item_id: UUID,
    body: ItemPatch,
    db: AsyncSession = Depends(get_db),
) -> dict:
    raise HTTPException(status_code=501, detail="Não implementado")
