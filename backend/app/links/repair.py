from __future__ import annotations

import json

import httpx
import structlog

from app.core.config import settings
from app.ia.base import ProviderError, RateLimitError

log = structlog.get_logger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.3-70b-versatile"
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.0-flash:generateContent"
)
_TIMEOUT = 20.0

_SYSTEM = (
    "Você é um assistente que sugere recursos educacionais reais disponíveis na internet. "
    "Responda APENAS com JSON válido, sem texto extra."
)


def _user_prompt(nome: str, tema: str, categoria: str, justificativa: str) -> str:
    return (
        f"Um plano de estudos sobre '{tema}' tem um item com link quebrado.\n\n"
        f"Item: {nome}\n"
        f"Categoria: {categoria}\n"
        f"Justificativa: {justificativa}\n\n"
        f"Sugira uma URL alternativa real e acessível para este conteúdo. "
        f"Use apenas URLs de sites conhecidos e estáveis (ex: Wikipedia, YouTube, "
        f"Coursera, edX, GitHub, documentação oficial). "
        f"Se não souber uma URL confiável, responda com null.\n\n"
        f'Responda SOMENTE com: {{"link": "https://..." }} ou {{"link": null}}'
    )


async def _chamar_groq(prompt: str) -> str | None:
    if not settings.groq_api_key:
        return None
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            _GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": _GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
        )
    if resp.status_code == 429:
        raise RateLimitError("Groq: quota esgotada")
    if resp.status_code != 200:
        raise ProviderError(f"Groq: HTTP {resp.status_code}")
    return resp.json()["choices"][0]["message"]["content"]


async def _chamar_gemini(prompt: str) -> str | None:
    if not settings.gemini_api_key:
        return None
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_GEMINI_URL}?key={settings.gemini_api_key}",
            json={
                "system_instruction": {"parts": [{"text": _SYSTEM}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.3,
                },
            },
        )
    if resp.status_code == 429:
        raise RateLimitError("Gemini: quota esgotada")
    if resp.status_code != 200:
        raise ProviderError(f"Gemini: HTTP {resp.status_code}")
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


async def buscar_substituto_ia(
    nome: str,
    tema: str,
    categoria: str,
    justificativa: str,
) -> str | None:
    """Ask the AI for a replacement URL. Returns a URL string or None."""
    prompt = _user_prompt(nome, tema, categoria, justificativa)

    raw: str | None = None
    try:
        raw = await _chamar_groq(prompt)
    except (RateLimitError, ProviderError) as exc:
        log.warning("repair_groq_falhou", error=str(exc))
        try:
            raw = await _chamar_gemini(prompt)
        except Exception as exc2:
            log.warning("repair_gemini_falhou", error=str(exc2))
            return None
    except Exception as exc:
        log.warning("repair_groq_erro", error=str(exc))
        return None

    if not raw:
        return None

    try:
        data = json.loads(raw)
        link = data.get("link")
        if isinstance(link, str) and link.startswith("http"):
            return link
    except Exception:
        log.warning("repair_parse_erro", raw=raw[:200])

    return None
