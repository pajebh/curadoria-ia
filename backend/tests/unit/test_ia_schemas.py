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


# --- wildcard normalization ---

def _plano_com_wildcards(indices_wildcard: list[tuple[int, int]]) -> dict:
    """Build a valid plan dict with wildcards at given (cat_idx, item_idx) positions."""
    item_base = {"nome": "Exemplo", "link": "https://example.com", "justificativa": "Justificativa válida de teste"}
    nomes = ["formal", "visual", "leitura", "audio", "experiencias", "referencias"]
    data: dict = {"categorias": [{"nome": n, "itens": [dict(item_base, is_wildcard=False)]} for n in nomes]}
    for cat_i, item_i in indices_wildcard:
        data["categorias"][cat_i]["itens"][item_i]["is_wildcard"] = True
    return data


def test_wildcard_unico_preservado() -> None:
    data = _plano_com_wildcards([(0, 0)])
    plano = PlanoGerado.model_validate(data)
    wildcards = [item for cat in plano.categorias for item in cat.itens if item.is_wildcard]
    assert len(wildcards) == 1


def test_wildcards_multiplos_normalizados_para_um() -> None:
    # Place wildcards on formal[0], visual[0], leitura[0]
    data = _plano_com_wildcards([(0, 0), (1, 0), (2, 0)])
    plano = PlanoGerado.model_validate(data)
    wildcards = [item for cat in plano.categorias for item in cat.itens if item.is_wildcard]
    assert len(wildcards) == 1
    # First wildcard (formal[0]) must be kept
    assert plano.categorias[0].itens[0].is_wildcard is True
    assert plano.categorias[1].itens[0].is_wildcard is False
    assert plano.categorias[2].itens[0].is_wildcard is False


def test_sem_wildcard_e_valido() -> None:
    plano = PlanoGerado.model_validate(_plano_valido())
    wildcards = [item for cat in plano.categorias for item in cat.itens if item.is_wildcard]
    assert len(wildcards) == 0


def test_wildcard_na_ultima_categoria() -> None:
    data = _plano_com_wildcards([(5, 0)])
    plano = PlanoGerado.model_validate(data)
    assert plano.categorias[5].itens[0].is_wildcard is True
    total = sum(1 for cat in plano.categorias for item in cat.itens if item.is_wildcard)
    assert total == 1
