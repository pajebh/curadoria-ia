import time

import structlog

from app.ia.base import IAProvider, ProviderError, RateLimitError
from app.ia.schemas import PlanoGerado

log = structlog.get_logger(__name__)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60) -> None:
        self._failures = 0
        self._threshold = failure_threshold
        self._timeout = timeout
        self._opened_at: float | None = None

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at > self._timeout:
            self._failures = 0
            self._opened_at = None
            return False
        return True

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = time.monotonic()
            log.warning("circuit_breaker_opened", failures=self._failures)

    def reset(self) -> None:
        self._failures = 0
        self._opened_at = None


class IAOrchestrator:
    def __init__(self, primary: IAProvider, fallback: IAProvider) -> None:
        self.primary = primary
        self.fallback = fallback
        self._cb = CircuitBreaker(failure_threshold=5, timeout=60)

    async def gerar_plano(self, tema: str, tempo: str) -> tuple[PlanoGerado, str]:
        if not self._cb.is_open():
            try:
                result = await self.primary.gerar_plano(tema, tempo)
                self._cb.reset()
                log.info("ia_provider_used", provider=self.primary.nome)
                return result, self.primary.nome
            except (RateLimitError, ProviderError) as exc:
                self._cb.record_failure()
                log.warning("primary_provider_failed", error=str(exc))

        log.info("ia_provider_used", provider=self.fallback.nome, reason="fallback")
        result = await self.fallback.gerar_plano(tema, tempo)
        return result, self.fallback.nome

    async def health(self) -> dict[str, str]:
        primary_ok = await self.primary.health()
        fallback_ok = await self.fallback.health()

        def status(ok: bool, cb_open: bool = False) -> str:
            if cb_open:
                return "degraded"
            return "ok" if ok else "down"

        return {
            self.primary.nome: status(primary_ok, self._cb.is_open()),
            self.fallback.nome: status(fallback_ok),
        }
