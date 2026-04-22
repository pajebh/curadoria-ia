from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_session, get_db_rls
from app.planos import repository as repo
from app.planos import service
from app.planos.schemas import ItemOut, ItemPatch, PlanoAccepted, PlanoCreate, PlanoOut
from app.planos.sse import sse_manager

router = APIRouter(prefix="/planos", tags=["planos"])


@router.post("", status_code=202, response_model=PlanoAccepted)
async def criar_plano(
    body: PlanoCreate,
    background_tasks: BackgroundTasks,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    session_id: UUID = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_rls),
) -> PlanoAccepted:
    return await service.criar_plano(db, session_id, body, idempotency_key, background_tasks)


@router.get("/{plano_id}/stream")
async def stream_plano(
    plano_id: UUID,
    session_id: UUID = Depends(get_current_session),
) -> StreamingResponse:
    plan_id_str = str(plano_id)
    if plan_id_str not in sse_manager._queues:
        sse_manager.create(plan_id_str)
    return StreamingResponse(
        sse_manager.subscribe(plan_id_str),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{plano_id}", response_model=PlanoOut)
async def obter_plano(
    plano_id: UUID,
    session_id: UUID = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_rls),
) -> PlanoOut:
    plan = await repo.obter_plan(db, plano_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return PlanoOut.model_validate(plan)


@router.delete("/{plano_id}", status_code=204)
async def apagar_plano(
    plano_id: UUID,
    session_id: UUID = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_rls),
) -> None:
    plan = await repo.obter_plan(db, plano_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    await repo.apagar_plan(db, plano_id)


@router.patch("/{plano_id}/itens/{item_id}", response_model=ItemOut)
async def patch_item(
    plano_id: UUID,
    item_id: UUID,
    body: ItemPatch,
    session_id: UUID = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_rls),
) -> ItemOut:
    item = await repo.atualizar_item(db, item_id, body.concluido)
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return ItemOut.model_validate(item)
