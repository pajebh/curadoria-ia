from typing import Protocol

from app.ia.schemas import PlanoGerado


class RateLimitError(Exception):
    pass


class ProviderError(Exception):
    pass


class IAProvider(Protocol):
    nome: str

    async def gerar_plano(self, tema: str, tempo: str) -> PlanoGerado: ...

    async def health(self) -> bool: ...
