import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PlanStatus(str, enum.Enum):
    pendente = "pendente"
    gerando = "gerando"
    concluido = "concluido"
    erro = "erro"


class TempoUnidade(str, enum.Enum):
    dias = "dias"
    semanas = "semanas"
    meses = "meses"


class CategoriaNome(str, enum.Enum):
    formal = "formal"
    visual = "visual"
    leitura = "leitura"
    audio = "audio"
    experiencias = "experiencias"
    referencias = "referencias"


class IAProvider(str, enum.Enum):
    groq = "groq"
    gemini = "gemini"


class LinkStatus(str, enum.Enum):
    unchecked = "unchecked"
    valid = "valid"
    broken = "broken"
    repaired = "repaired"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    tema: Mapped[str] = mapped_column(Text, nullable=False)
    tempo_valor: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo_unidade: Mapped[TempoUnidade] = mapped_column(
        Enum(TempoUnidade, name="tempo_unidade"), nullable=False
    )
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status"), nullable=False, default=PlanStatus.pendente
    )
    ia_provider: Mapped[IAProvider | None] = mapped_column(
        Enum(IAProvider, name="ia_provider"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    categorias: Mapped[list["PlanCategory"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("char_length(tema) BETWEEN 3 AND 200", name="ck_plans_tema_len"),
        CheckConstraint("tempo_valor BETWEEN 1 AND 24", name="ck_plans_tempo_valor"),
        Index("idx_plans_session", "session_id", "criado_em"),
        Index(
            "idx_plans_status",
            "status",
            postgresql_where="status IN ('pendente', 'gerando')",
        ),
    )


class PlanCategory(Base):
    __tablename__ = "plan_categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[CategoriaNome] = mapped_column(
        Enum(CategoriaNome, name="categoria_nome"), nullable=False
    )
    ordem: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    plan: Mapped["Plan"] = relationship(back_populates="categorias")
    itens: Mapped[list["PlanItem"]] = relationship(
        back_populates="categoria", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("plan_id", "nome", name="uq_categories_plan_nome"),
        Index("idx_categories_plan", "plan_id"),
    )


class PlanItem(Base):
    __tablename__ = "plan_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("plan_categories.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=False)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    concluido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ordem: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_wildcard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    link_status: Mapped[LinkStatus] = mapped_column(
        Enum(LinkStatus, name="link_status"), nullable=False, default=LinkStatus.unchecked
    )

    categoria: Mapped["PlanCategory"] = relationship(back_populates="itens")

    __table_args__ = (
        CheckConstraint("link ~ '^https?://'", name="ck_items_link_url"),
        Index("idx_items_category", "category_id", "ordem"),
        Index(
            "idx_items_wildcard",
            "category_id",
            postgresql_where="is_wildcard = true",
        ),
        Index(
            "idx_items_broken",
            "id",
            postgresql_where="link_status = 'broken'",
        ),
    )


class PlanEvent(Base):
    __tablename__ = "plan_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (Index("idx_events_plan", "plan_id", "criado_em"),)


class LGPDDeletion(Base):
    __tablename__ = "lgpd_deletions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_hash: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    executed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    items_deleted: Mapped[int | None] = mapped_column(Integer, nullable=True)
