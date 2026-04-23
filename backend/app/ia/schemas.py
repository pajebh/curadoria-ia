from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

CATEGORIAS_OBRIGATORIAS = {"formal", "visual", "leitura", "audio", "experiencias", "referencias"}


class ItemGerado(BaseModel):
    nome: str = Field(min_length=3, max_length=200)
    link: HttpUrl
    justificativa: str = Field(min_length=10, max_length=500)
    is_wildcard: bool = False


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

    @model_validator(mode="after")
    def normalizar_wildcard(self) -> "PlanoGerado":
        # Ensure at most 1 wildcard across the whole plan.
        # If the LLM marks multiple, keep the first and reset the rest.
        found_first = False
        for categoria in self.categorias:
            for item in categoria.itens:
                if item.is_wildcard:
                    if found_first:
                        item.is_wildcard = False
                    else:
                        found_first = True
        return self
