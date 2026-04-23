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
async def test_validar_item_link_quebrado_ia_repara() -> None:
    from app.links.validator import _validar_item
    import asyncio

    item = _make_item(link="https://broken.example.com", nome="Curso de Python")
    sem = asyncio.Semaphore(5)
    novo_url = "https://docs.python.org/3/tutorial/"

    with (
        patch("app.links.validator._head_ok", AsyncMock(side_effect=[False, True])),
        patch("app.links.validator.buscar_substituto_ia", AsyncMock(return_value=novo_url)),
    ):
        item_id, status, novo_link = await _validar_item(item, "Python", sem)

    assert status == LinkStatus.repaired
    assert novo_link == novo_url


@pytest.mark.asyncio
async def test_validar_item_link_quebrado_ia_falha() -> None:
    from app.links.validator import _validar_item
    import asyncio

    item = _make_item(link="https://broken.example.com", nome="Curso Inexistente")
    sem = asyncio.Semaphore(5)

    with (
        patch("app.links.validator._head_ok", AsyncMock(return_value=False)),
        patch("app.links.validator.buscar_substituto_ia", AsyncMock(return_value=None)),
    ):
        item_id, status, novo_link = await _validar_item(item, "Python", sem)

    assert status == LinkStatus.broken
    assert novo_link is None


@pytest.mark.asyncio
async def test_validar_item_link_quebrado_substituto_tambem_quebrado() -> None:
    from app.links.validator import _validar_item
    import asyncio

    item = _make_item(link="https://broken.example.com", nome="Curso Inexistente")
    sem = asyncio.Semaphore(5)
    substituto = "https://also-broken.example.com"

    with (
        patch("app.links.validator._head_ok", AsyncMock(return_value=False)),
        patch("app.links.validator.buscar_substituto_ia", AsyncMock(return_value=substituto)),
    ):
        item_id, status, novo_link = await _validar_item(item, "Python", sem)

    assert status == LinkStatus.broken
    assert novo_link is None
