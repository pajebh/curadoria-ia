from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ia.schemas import PlanoGerado
from app.planos.models import (
    CategoriaNome,
    IAProvider,
    LinkStatus,
    Plan,
    PlanCategory,
    PlanItem,
    PlanStatus,
    TempoUnidade,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def criar_plan(
    db: AsyncSession,
    session_id: UUID,
    tema: str,
    tempo_valor: int,
    tempo_unidade: TempoUnidade,
) -> Plan:
    plan = Plan(
        session_id=session_id,
        tema=tema,
        tempo_valor=tempo_valor,
        tempo_unidade=tempo_unidade,
        status=PlanStatus.pendente,
        criado_em=_utcnow(),
        atualizado_em=_utcnow(),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def obter_plan(db: AsyncSession, plan_id: UUID) -> Plan | None:
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.categorias).selectinload(PlanCategory.itens))
        .where(Plan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def apagar_plan(db: AsyncSession, plan_id: UUID) -> None:
    plan = await db.get(Plan, plan_id)
    if plan:
        await db.delete(plan)
        await db.commit()


async def listar_planos_sessao(
    db: AsyncSession,
    session_id: UUID,
    cursor: UUID | None = None,
    limit: int = 20,
) -> tuple[list[Plan], UUID | None]:
    q = (
        select(Plan)
        .where(Plan.session_id == session_id)
        .order_by(Plan.criado_em.desc())  # type: ignore[attr-defined]
    )
    if cursor is not None:
        cursor_plan = await db.get(Plan, cursor)
        if cursor_plan and cursor_plan.criado_em is not None:
            q = q.where(Plan.criado_em < cursor_plan.criado_em)
    q = q.limit(limit + 1)
    result = await db.execute(q)
    items = list(result.scalars())
    next_cursor: UUID | None = None
    if len(items) > limit:
        next_cursor = items[limit].id
        items = items[:limit]
    return items, next_cursor


async def salvar_categorias_e_itens(
    db: AsyncSession, plan_id: UUID, plano_gerado: PlanoGerado
) -> None:
    for ordem_cat, cat_gerada in enumerate(plano_gerado.categorias):
        categoria = PlanCategory(
            plan_id=plan_id,
            nome=CategoriaNome(cat_gerada.nome),
            ordem=ordem_cat,
        )
        db.add(categoria)
        await db.flush()
        for ordem_item, item_gerado in enumerate(cat_gerada.itens):
            item = PlanItem(
                category_id=categoria.id,
                nome=item_gerado.nome,
                link=str(item_gerado.link),
                justificativa=item_gerado.justificativa,
                concluido=False,
                ordem=ordem_item,
                is_wildcard=item_gerado.is_wildcard,
            )
            db.add(item)
    await db.commit()


async def atualizar_status(
    db: AsyncSession,
    plan_id: UUID,
    status: PlanStatus,
    ia_provider: str | None = None,
) -> None:
    values: dict = {"status": status, "atualizado_em": _utcnow()}
    if ia_provider is not None:
        values["ia_provider"] = IAProvider(ia_provider)
    await db.execute(update(Plan).where(Plan.id == plan_id).values(**values))
    await db.commit()


async def atualizar_item(
    db: AsyncSession, item_id: UUID, concluido: bool
) -> PlanItem | None:
    item = await db.get(PlanItem, item_id)
    if item is None:
        return None
    item.concluido = concluido
    await db.commit()
    await db.refresh(item)
    return item


async def atualizar_link_item(
    db: AsyncSession,
    item_id: UUID,
    status: LinkStatus,
    novo_link: str | None = None,
) -> None:
    item = await db.get(PlanItem, item_id)
    if item is None:
        return
    item.link_status = status
    if novo_link is not None:
        item.link = novo_link
    await db.commit()


async def listar_itens_plano(db: AsyncSession, plan_id: UUID) -> list[PlanItem]:
    result = await db.execute(
        select(PlanItem)
        .join(PlanCategory, PlanItem.category_id == PlanCategory.id)
        .where(PlanCategory.plan_id == plan_id)
    )
    return list(result.scalars())


async def listar_itens_para_revalidar(
    db: AsyncSession,
    limite: int = 500,
) -> list[PlanItem]:
    """Items from completed plans (last 180d) with valid/repaired status — for weekly cron."""
    cutoff = _utcnow() - __import__("datetime").timedelta(days=180)
    result = await db.execute(
        select(PlanItem)
        .join(PlanCategory, PlanItem.category_id == PlanCategory.id)
        .join(Plan, PlanCategory.plan_id == Plan.id)
        .where(
            Plan.status == PlanStatus.concluido,
            Plan.criado_em >= cutoff,
            PlanItem.link_status.in_([LinkStatus.valid, LinkStatus.repaired]),
        )
        .limit(limite)
    )
    return list(result.scalars())
