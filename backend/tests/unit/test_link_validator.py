from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.planos.models import LinkStatus


def _make_item(link: str = "https://example.com", nome: str = "Item") -> MagicMock:
    item = MagicMock()
    item.id = uuid4()
    item.link = link
    item.nome = nome
    item.justificativa = "Justificativa de teste"
    item.categoria = MagicMock()
    item.categoria.nome = MagicMock()
    item.categoria.nome.value = "formal"
    return item


# --- _head_ok ---

@pytest.mark.asyncio
async def test_head_ok_retorna_true_para_2xx() -> None:
    from app.links.validator import _head_ok

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("app.links.validator.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.head = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await _head_ok("https://example.com")

    assert result is True


@pytest.mark.asyncio
async def test_head_ok_retorna_false_para_404() -> None:
    from app.links.validator import _head_ok

    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("app.links.validator.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.head = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await _head_ok("https://broken.example.com/404")

    assert result is False


@pytest.mark.asyncio
async def test_head_ok_retorna_false_em_excecao() -> None:
    from app.links.validator import _head_ok

    with patch("app.links.validator.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.head = AsyncMock(side_effect=Exception("timeout"))
        mock_client_cls.return_value = mock_client

        result = await _head_ok("https://timeout.example.com")

    assert result is False


# --- gerar_url_busca ---

def test_gerar_url_busca_formal() -> None:
    from app.links.repair import gerar_url_busca

    url = gerar_url_busca("Técnica de Saque", "Beach Tennis", "formal")
    assert "youtube.com/results" in url
    assert "Beach+Tennis" in url or "Beach Tennis" in url.replace("+", " ")


def test_gerar_url_busca_audio() -> None:
    from app.links.repair import gerar_url_busca

    url = gerar_url_busca("Podcast de Esporte", "Beach Tennis", "audio")
    assert "spotify.com/search" in url


def test_gerar_url_busca_categoria_desconhecida() -> None:
    from app.links.repair import gerar_url_busca

    url = gerar_url_busca("Qualquer Item", "Tema", "desconhecida")
    assert url.startswith("https://www.google.com/search")


# --- _validar_item ---

@pytest.mark.asyncio
async def test_validar_item_link_valido() -> None:
    from app.links.validator import _validar_item
    import asyncio

    item = _make_item()
    sem = asyncio.Semaphore(5)

    with patch("app.links.validator._head_ok", AsyncMock(return_value=True)):
        item_id, status, novo_link = await _validar_item(item, "Python", sem)

    assert status == LinkStatus.valid
    assert novo_link is None
    assert item_id == item.id


@pytest.mark.asyncio
async def test_validar_item_link_quebrado_gera_url_busca() -> None:
    from app.links.validator import _validar_item
    import asyncio

    item = _make_item(link="https://broken.example.com", nome="Curso de Python")
    sem = asyncio.Semaphore(5)

    with patch("app.links.validator._head_ok", AsyncMock(return_value=False)):
        item_id, status, novo_link = await _validar_item(item, "Python", sem)

    assert status == LinkStatus.repaired
    assert novo_link is not None
    assert novo_link.startswith("https://")
    assert "python" in novo_link.lower() or "Python" in novo_link
