from pydantic import BaseModel, Field, HttpUrl, field_validator

CATEGORIAS_OBRIGATORIAS = {"formal", "visual", "leitura", "audio", "experiencias", "referencias"}


class ItemGerado(BaseModel):
    nome: str = Field(min_length=3, max_length=200)
    link: HttpUrl
    justificativa: str = Field(min_length=10, max_length=500)


class CategoriaGerada(BaseModel):
    nome: str
    itens: list[ItemGerado] = Field(min_length=1, max_length=8)


class PlanoGerado(BaseModel):
    categorias: list[CategoriaGerada]

    @field_validator("categorias")
    @classmethod
    def todas_categorias_presentes(cls, v: list[CategoriaGerada]) -> list[CategoriaGerada]:
        nomes = {c.nome for c in v}
        faltando = CATEGORIAS_OBRIGATORIAS - nomes
        if faltando:
            raise ValueError(f"Categorias obrigatórias ausentes: {sorted(faltando)}")
        extras = nomes - CATEGORIAS_OBRIGATORIAS
        if extras:
            raise ValueError(f"Categorias não reconhecidas: {sorted(extras)}")
        return v
