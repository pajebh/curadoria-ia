from uuid import UUID

import structlog
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.idempotency import idempotency_check, idempotency_store
from app.ia.gemini_provider import GeminiProvider
from app.ia.groq_provider import GroqProvider
from app.ia.moderacao import LocalizacaoInseguraError, TemaInseguroError, validar_localizacao, validar_tema
from app.ia.orchestrator import IAOrchestrator
from app.ia.prompt import render_user_prompt
from app.planos.models import PlanStatus, TempoUnidade
from app.planos.repository import (
    atualizar_status,
    criar_plan,
    salvar_categorias_e_itens,
)
from app.planos.schemas import ContextoUsuario, PlanoAccepted, PlanoCreate
from app.planos.sse import sse_manager

log = structlog.get_logger(__name__)

_orchestrator = IAOrchestrator(primary=GroqProvider(), fallback=GeminiProvider())


async def criar_plano(
    db: AsyncSession,
    session_id: UUID,
    body: PlanoCreate,
    idempotency_key: UUID,
    background_tasks: BackgroundTasks,
) -> PlanoAccepted:
    key = str(idempotency_key)
    existing = await idempotency_check(key, session_id)
    if existing:
        return PlanoAccepted(
            plano_id=existing,
            stream_url=f"/v1/planos/{existing}/stream",
        )

    try:
        validar_tema(body.tema)
    except TemaInseguroError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if body.contexto and body.contexto.localizacao:
        try:
            validar_localizacao(body.contexto.localizacao)
        except LocalizacaoInseguraError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    plan = await criar_plan(
        db, session_id, body.tema, body.tempo_valor, body.tempo_unidade
    )
    await idempotency_store(key, session_id, plan.id)
    sse_manager.create(str(plan.id))
    background_tasks.add_task(_gerar_plano_bg, plan.id, body)

    return PlanoAccepted(
        plano_id=plan.id,
        stream_url=f"/v1/planos/{plan.id}/stream",
    )


async def _gerar_plano_bg(plan_id: UUID, body: PlanoCreate) -> None:
    from app.core.db import AsyncSessionLocal

    contexto: ContextoUsuario | None = body.contexto if (
        body.contexto and body.contexto.tem_dados()
    ) else None

    sse_manager.publish(
        str(plan_id), {"event": "progress", "stage": "moderacao", "percent": 10}
    )

    async with AsyncSessionLocal() as db:
        try:
            sse_manager.publish(
                str(plan_id), {"event": "progress", "stage": "gerando", "percent": 30}
            )

            tempo_unidade = (
                body.tempo_unidade.value
                if isinstance(body.tempo_unidade, TempoUnidade)
                else str(body.tempo_unidade)
            )
            user_prompt = render_user_prompt(
                body.tema, body.tempo_valor, tempo_unidade, contexto
            )
            plano_gerado, provider = await _orchestrator.gerar_plano(body.tema, user_prompt)

            # If no contexto was provided, zero out any wildcards the LLM may have added
            if contexto is None:
                for cat in plano_gerado.categorias:
                    for item in cat.itens:
                        item.is_wildcard = False

            sse_manager.publish(
                str(plan_id), {"event": "progress", "stage": "validando", "percent": 80}
            )

            await salvar_categorias_e_itens(db, plan_id, plano_gerado)
            await atualizar_status(db, plan_id, PlanStatus.concluido, provider)

            sse_manager.publish(str(plan_id), {"event": "done", "percent": 100})
            log.info("plano_gerado", plan_id=str(plan_id), provider=provider,
                     com_contexto=contexto is not None)

        except Exception as exc:
            log.error("plano_erro", plan_id=str(plan_id), error=str(exc))
            try:
                await atualizar_status(db, plan_id, PlanStatus.erro)
            except Exception:
                pass
            sse_manager.publish(
                str(plan_id), {"event": "erro", "message": "Erro na geração do plano"}
            )
        finally:
            sse_manager.publish(str(plan_id), None)
