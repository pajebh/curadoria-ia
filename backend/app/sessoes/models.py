from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import Index, Text
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
