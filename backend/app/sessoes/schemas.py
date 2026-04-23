from datetime import datetime

from pydantic import BaseModel

from app.sessoes.models import (
    IdiomaPref,
    MotivacaoPref,
    NivelConhecimento,
    OrcamentoPref,
    RotinaPref,
)


class PerfilUpdate(BaseModel):
    nivel: NivelConhecimento | None = None
    orcamento: OrcamentoPref | None = None
    idioma: IdiomaPref | None = None
    rotina: RotinaPref | None = None
    motivacao: MotivacaoPref | None = None


class PerfilOut(BaseModel):
    nivel: NivelConhecimento | None = None
    orcamento: OrcamentoPref | None = None
    idioma: IdiomaPref | None = None
    rotina: RotinaPref | None = None
    motivacao: MotivacaoPref | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}
