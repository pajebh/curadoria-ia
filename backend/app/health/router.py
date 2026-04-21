from fastapi import APIRouter

from app.ia.gemini_provider import GeminiProvider
from app.ia.groq_provider import GroqProvider
from app.ia.orchestrator import IAOrchestrator

router = APIRouter(prefix="/health", tags=["health"])

_orchestrator = IAOrchestrator(primary=GroqProvider(), fallback=GeminiProvider())


@router.get("/ia")
async def health_ia() -> dict[str, str]:
    return await _orchestrator.health()
