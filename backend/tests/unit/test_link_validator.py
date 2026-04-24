from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.planos.models import LinkStatus


def _make_item(
    link: str = "https://example.com",
    nome: str = "Item",
    categoria_nome: str = "formal",
) -> MagicMock:
    item = MagicMock()
    item.id = uuid4()
    item.link = link
    item.nome = nome
    item.justificativa = "Justificativa de teste"
    item.categoria = MagicMock()
    item.categoria.nome = MagicMock()
    item.categoria.nome.value = categoria_nome
    return item


# --- gerar_url_busca ---

def test_gerar_url_busca_formal() -> None:
    from app.links.repair import gerar_url_busca

    url = gerar_url_busca("Técnica de Saque", "Beach Tennis", "formal")
    assert "youtube.com/results" in url


def test_gerar_url_busca_audio() -> None:
    from app.links.repair import gerar_url_busca

    url = gerar_url_busca("Podcast de Esporte", "Beach Tennis", "audio")
    assert "spotify.com/search" in url


def test_gerar_url_busca_categoria_desconhecida() -> None:
    from app.links.repair import gerar_url_busca

    url = gerar_url_busca("Qualquer Item", "Tema", "desconhecida")
    assert url.startswith("https://www.google.com/search")


# --- _enriquecer_item ---

@pytest.mark.asyncio
async def test_enriquecer_item_formal_usa_youtube() -> None:
    from app.links.validator import _enriquecer_item
    import asyncio

    item = _make_item(categoria_nome="formal", nome="Saque")
    sem = asyncio.Semaphore(5)
    youtube_url = "https://www.youtube.com/watch?v=abc123"

    with patch(
        "app.links.validator.buscar_youtube", AsyncMock(return_value=youtube_url)
    ):
        item_id, status, novo_link = await _enriquecer_item(item, "Beach Tennis", sem)

    assert status == LinkStatus.repaired
    assert novo_link == youtube_url


@pytest.mark.asyncio
async def test_enriquecer_item_audio_usa_itunes() -> None:
    from app.links.validator import _enriquecer_item
    import asyncio

    item = _make_item(categoria_nome="audio", nome="Podcast Técnica")
    sem = asyncio.Semaphore(5)
    itunes_url = "https://podcasts.apple.com/br/podcast/xyz"

    with patch(
        "app.links.validator.buscar_itunes", AsyncMock(return_value=itunes_url)
    ):
        item_id, status, novo_link = await _enriquecer_item(item, "Beach Tennis", sem)

    assert status == LinkStatus.repaired
    assert novo_link == itunes_url


@pytest.mark.asyncio
async def test_enriquecer_item_referencias_usa_wikipedia() -> None:
    from app.links.validator import _enriquecer_item
    import asyncio

    item = _make_item(categoria_nome="referencias", nome="História")
    sem = asyncio.Semaphore(5)
    wiki_url = "https://pt.wikipedia.org/wiki/Beach_Tennis"

    with patch(
        "app.links.validator.buscar_wikipedia", AsyncMock(return_value=wiki_url)
    ):
        item_id, status, novo_link = await _enriquecer_item(item, "Beach Tennis", sem)

    assert status == LinkStatus.repaired
    assert novo_link == wiki_url


@pytest.mark.asyncio
async def test_enriquecer_item_leitura_tenta_openlibrary_depois_wikipedia() -> None:
    from app.links.validator import _enriquecer_item
    import asyncio

    item = _make_item(categoria_nome="leitura", nome="Livro")
    sem = asyncio.Semaphore(5)
    wiki_url = "https://pt.wikipedia.org/wiki/Livro"

    with (
        patch("app.links.validator.buscar_openlibrary", AsyncMock(return_value=None)),
        patch("app.links.validator.buscar_wikipedia", AsyncMock(return_value=wiki_url)),
    ):
        item_id, status, novo_link = await _enriquecer_item(item, "Tema", sem)

    assert status == LinkStatus.repaired
    assert novo_link == wiki_url


@pytest.mark.asyncio
async def test_enriquecer_item_fallback_para_busca_google() -> None:
    from app.links.validator import _enriquecer_item
    import asyncio

    item = _make_item(categoria_nome="formal", nome="Item Obscuro")
    sem = asyncio.Semaphore(5)

    with patch("app.links.validator.buscar_youtube", AsyncMock(return_value=None)):
        item_id, status, novo_link = await _enriquecer_item(item, "Tema Raro", sem)

    assert status == LinkStatus.repaired
    assert novo_link is not None
    assert novo_link.startswith("https://")


@pytest.mark.asyncio
async def test_enriquecer_item_experiencias_vai_direto_para_google() -> None:
    from app.links.validator import _enriquecer_item
    import asyncio

    item = _make_item(categoria_nome="experiencias", nome="Torneio Local")
    sem = asyncio.Semaphore(5)

    item_id, status, novo_link = await _enriquecer_item(item, "Beach Tennis", sem)

    assert status == LinkStatus.repaired
    assert novo_link is not None
    assert "google.com/search" in novo_link
