import json

import httpx
import structlog

from app.core.config import settings
from app.ia.base import ProviderError, RateLimitError
from app.ia.prompt import SYSTEM, render_user_prompt
from app.ia.schemas import PlanoGerado

log = structlog.get_logger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"


class GroqProvider:
    nome = "groq"

    async def gerar_plano(self, tema: str, tempo: str) -> PlanoGerado:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": tempo},  # tempo já renderizado no prompt
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"},
                },
            )

        if response.status_code == 429:
            raise RateLimitError("Groq: quota esgotada")
        if response.status_code != 200:
            raise ProviderError(f"Groq: HTTP {response.status_code}")

        content = response.json()["choices"][0]["message"]["content"]
        return PlanoGerado.model_validate(json.loads(content))

    async def health(self) -> bool:
        if not settings.groq_api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                )
            return r.status_code == 200
        except Exception:
            return False
