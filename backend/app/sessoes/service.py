from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_session_token, hash_token
from app.sessoes.models import Session, SessionProfile
from app.sessoes.schemas import PerfilUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    now = _utcnow()
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(last_seen_at=now)
    )
    await db.commit()


async def obter_perfil(db: AsyncSession, session_id: UUID) -> SessionProfile | None:
    return await db.get(SessionProfile, session_id)


async def upsert_perfil(
    db: AsyncSession,
    session_id: UUID,
    data: PerfilUpdate,
) -> SessionProfile:
    # COALESCE merge: NULL in payload preserves existing value
    await db.execute(
        text("""
            INSERT INTO session_profiles
                (session_id, nivel, orcamento, idioma, rotina, motivacao, atualizado_em)
            VALUES
                (:session_id, :nivel, :orcamento, :idioma, :rotina, :motivacao, :now)
            ON CONFLICT (session_id) DO UPDATE SET
                nivel       = COALESCE(EXCLUDED.nivel,     session_profiles.nivel),
                orcamento   = COALESCE(EXCLUDED.orcamento, session_profiles.orcamento),
                idioma      = COALESCE(EXCLUDED.idioma,    session_profiles.idioma),
                rotina      = COALESCE(EXCLUDED.rotina,    session_profiles.rotina),
                motivacao   = COALESCE(EXCLUDED.motivacao, session_profiles.motivacao),
                atualizado_em = EXCLUDED.atualizado_em
        """),
        {
            "session_id": str(session_id),
            "nivel": data.nivel.value if data.nivel else None,
            "orcamento": data.orcamento.value if data.orcamento else None,
            "idioma": data.idioma.value if data.idioma else None,
            "rotina": data.rotina.value if data.rotina else None,
            "motivacao": data.motivacao.value if data.motivacao else None,
            "now": _utcnow(),
        },
    )
    await db.commit()

    perfil = await db.get(SessionProfile, session_id)
    if perfil is None:
        raise RuntimeError(f"upsert_perfil: profile not found after upsert for session {session_id}")
    return perfil
