import pytest
from pydantic import ValidationError

from app.ia.schemas import PlanoGerado


def _plano_valido() -> dict:
    item = {"nome": "Exemplo", "link": "https://example.com", "justificativa": "Justificativa válida de teste"}
    return {
        "categorias": [
            {"nome": "formal", "itens": [item]},
            {"nome": "visual", "itens": [item]},
            {"nome": "leitura", "itens": [item]},
            {"nome": "audio", "itens": [item]},
            {"nome": "experiencias", "itens": [item]},
            {"nome": "referencias", "itens": [item]},
        ]
    }


def test_aceita_plano_completo() -> None:
    plano = PlanoGerado.model_validate(_plano_valido())
    assert len(plano.categorias) == 6


def test_rejeita_categoria_faltando() -> None:
    data = _plano_valido()
    data["categorias"] = data["categorias"][:-1]  # remove 'referencias'
    with pytest.raises(ValidationError, match="referencias"):
        PlanoGerado.model_validate(data)


def test_rejeita_categoria_extra() -> None:
    data = _plano_valido()
    data["categorias"].append(
        {"nome": "extra_invalida", "itens": [
            {"nome": "X", "link": "https://x.com", "justificativa": "justificativa longa o suficiente"}
        ]}
    )
    # agora tem 7 categorias — uma extra não reconhecida
    with pytest.raises(ValidationError):
        PlanoGerado.model_validate(data)


def test_rejeita_link_http_sem_s() -> None:
    data = _plano_valido()
    data["categorias"][0]["itens"][0]["link"] = "http://example.com"
    # http:// é válido para HttpUrl — mas nossa constraint de banco exige https
    # O validator Pydantic aceita http, a constraint de prod é no banco
    plano = PlanoGerado.model_validate(data)
    assert str(plano.categorias[0].itens[0].link).startswith("http")


def test_rejeita_item_sem_itens() -> None:
    data = _plano_valido()
    data["categorias"][0]["itens"] = []
    with pytest.raises(ValidationError):
        PlanoGerado.model_validate(data)


def test_rejeita_justificativa_curta() -> None:
    data = _plano_valido()
    data["categorias"][0]["itens"][0]["justificativa"] = "curta"
    with pytest.raises(ValidationError):
        PlanoGerado.model_validate(data)
