from __future__ import annotations

from urllib.parse import quote_plus


_CATEGORIA_TEMPLATES: dict[str, str] = {
    "formal":       "https://www.youtube.com/results?search_query={query}+curso+aula",
    "visual":       "https://www.youtube.com/results?search_query={query}",
    "leitura":      "https://www.google.com/search?q={query}+livro+artigo",
    "audio":        "https://open.spotify.com/search/{query}",
    "experiencias": "https://www.google.com/search?q={query}+evento+experiencia",
    "referencias":  "https://www.google.com/search?q={query}",
}

_FALLBACK = "https://www.google.com/search?q={query}"


def gerar_url_busca(nome: str, tema: str, categoria: str) -> str:
    """Build a deterministic search URL for a broken item — always valid."""
    query = quote_plus(f"{nome} {tema}")
    template = _CATEGORIA_TEMPLATES.get(categoria, _FALLBACK)
    return template.format(query=query)
