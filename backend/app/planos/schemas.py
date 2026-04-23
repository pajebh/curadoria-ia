from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.planos.models import CategoriaNome, PlanStatus, TempoUnidade
from app.sessoes.models import (
    IdiomaPref,
    MotivacaoPref,
    NivelConhecimento,
    OrcamentoPref,
    RotinaPref,
)


class ContextoUsuario(BaseModel):
    nivel: NivelConhecimento | None = None
    orcamento: OrcamentoPref | None = None
    idioma: IdiomaPref | None = None
    rotina: RotinaPref | None = None
    localizacao: str | None = Field(default=None, max_length=100)
    motivacao: MotivacaoPref | None = None

    def tem_dados(self) -> bool:
        return any(
            v is not None
            for v in (self.nivel, self.orcamento, self.idioma,
                      self.rotina, self.localizacao, self.motivacao)
        )


class PlanoCreate(BaseModel):
    tema: str = Field(min_length=3, max_length=200)
    tempo_valor: int = Field(ge=1, le=24)
    tempo_unidade: TempoUnidade
    contexto: ContextoUsuario | None = None


class ItemOut(BaseModel):
    id: UUID
    nome: str
    link: str
    justificativa: str
    concluido: bool
    ordem: int
    is_wildcard: bool

    model_config = {"from_attributes": True}


class CategoriaOut(BaseModel):
    id: UUID
    nome: CategoriaNome
    ordem: int
    itens: list[ItemOut] = []

    model_config = {"from_attributes": True}


class PlanoOut(BaseModel):
    id: UUID
    tema: str
    tempo_valor: int
    tempo_unidade: TempoUnidade
    status: PlanStatus
    ia_provider: str | None = None
    categorias: list[CategoriaOut] = []

    model_config = {"from_attributes": True}


class PlanoAccepted(BaseModel):
    plano_id: UUID
    stream_url: str


class ItemPatch(BaseModel):
    concluido: bool


class PlanoResumo(BaseModel):
    id: UUID
    tema: str
    tempo_valor: int
    tempo_unidade: TempoUnidade
    status: PlanStatus
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}
