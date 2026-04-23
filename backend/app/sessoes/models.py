import enum
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=_utcnow, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        default=_utcnow, nullable=False
    )
    purge_at: Mapped[datetime] = mapped_column(
        default=lambda: _utcnow() + timedelta(days=180),
        nullable=False,
    )

    __table_args__ = (Index("idx_sessions_purge_at", "purge_at"),)


# ── Enums de personalização ────────────────────────────────────────────────────

class NivelConhecimento(str, enum.Enum):
    zero = "zero"
    basico = "basico"
    intermediario = "intermediario"
    avancado = "avancado"


class OrcamentoPref(str, enum.Enum):
    gratuito = "gratuito"
    aberto_a_investimentos = "aberto_a_investimentos"


class IdiomaPref(str, enum.Enum):
    apenas_portugues = "apenas_portugues"
    aceita_ingles = "aceita_ingles"
    aceita_outros = "aceita_outros"


class RotinaPref(str, enum.Enum):
    prefere_ler = "prefere_ler"
    prefere_ouvir = "prefere_ouvir"
    prefere_assistir = "prefere_assistir"


class MotivacaoPref(str, enum.Enum):
    carreira = "carreira"
    hobby = "hobby"
    curiosidade = "curiosidade"
    repertorio_social = "repertorio_social"


class SessionProfile(Base):
    __tablename__ = "session_profiles"

    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    nivel: Mapped[NivelConhecimento | None] = mapped_column(
        Enum(NivelConhecimento, name="nivel_conhecimento"),
        nullable=True,
    )
    orcamento: Mapped[OrcamentoPref | None] = mapped_column(
        Enum(OrcamentoPref, name="orcamento_pref"),
        nullable=True,
    )
    idioma: Mapped[IdiomaPref | None] = mapped_column(
        Enum(IdiomaPref, name="idioma_pref"),
        nullable=True,
    )
    rotina: Mapped[RotinaPref | None] = mapped_column(
        Enum(RotinaPref, name="rotina_pref"),
        nullable=True,
    )
    motivacao: Mapped[MotivacaoPref | None] = mapped_column(
        Enum(MotivacaoPref, name="motivacao_pref"),
        nullable=True,
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        default=_utcnow, nullable=False
    )
