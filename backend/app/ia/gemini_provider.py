import json

import httpx
import structlog

from app.core.config import settings
from app.ia.base import ProviderError, RateLimitError
from app.ia.prompt import SYSTEM, render_user_prompt
from app.ia.schemas import PlanoGerado

log = structlog.get_logger(__name__)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.0-flash:generateContent"
)


class GeminiProvider:
    nome = "gemini"

    async def gerar_plano(self, tema: str, tempo: str) -> PlanoGerado:
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={settings.gemini_api_key}",
                json={
                    "system_instruction": {"parts": [{"text": SYSTEM}]},
                    "contents": [{"parts": [{"text": tempo}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.7,
                    },
                },
            )

        if response.status_code == 429:
            raise RateLimitError("Gemini: quota esgotada")
        if response.status_code != 200:
            raise ProviderError(f"Gemini: HTTP {response.status_code}")

        content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return PlanoGerado.model_validate(json.loads(content))

    async def health(self) -> bool:
        if not settings.gemini_api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models"
                    f"?key={settings.gemini_api_key}"
                )
            return r.status_code == 200
        except Exception:
            return False
