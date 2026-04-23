import pytest
from pydantic import ValidationError

from app.planos.schemas import ContextoUsuario, PlanoCreate
from app.sessoes.models import (
    IdiomaPref,
    MotivacaoPref,
    NivelConhecimento,
    OrcamentoPref,
    RotinaPref,
)


# --- ContextoUsuario.tem_dados() ---

def test_tem_dados_retorna_false_quando_tudo_none() -> None:
    ctx = ContextoUsuario()
    assert ctx.tem_dados() is False


def test_tem_dados_retorna_true_com_nivel() -> None:
    ctx = ContextoUsuario(nivel=NivelConhecimento.basico)
    assert ctx.tem_dados() is True


def test_tem_dados_retorna_true_com_localizacao() -> None:
    ctx = ContextoUsuario(localizacao="São Paulo, SP")
    assert ctx.tem_dados() is True


def test_tem_dados_retorna_true_com_qualquer_campo() -> None:
    for ctx in [
        ContextoUsuario(orcamento=OrcamentoPref.gratuito),
        ContextoUsuario(idioma=IdiomaPref.aceita_ingles),
        ContextoUsuario(rotina=RotinaPref.prefere_ouvir),
        ContextoUsuario(motivacao=MotivacaoPref.carreira),
    ]:
        assert ctx.tem_dados() is True


# --- ContextoUsuario validations ---

def test_localizacao_max_100_chars() -> None:
    ctx = ContextoUsuario(localizacao="a" * 100)
    assert len(ctx.localizacao or "") == 100


def test_localizacao_rejeita_acima_100_chars() -> None:
    with pytest.raises(ValidationError):
        ContextoUsuario(localizacao="a" * 101)


def test_contexto_rejeita_enum_invalido() -> None:
    with pytest.raises(ValidationError):
        ContextoUsuario(nivel="invalido")  # type: ignore[arg-type]


# --- PlanoCreate com contexto ---

def _base_plano() -> dict:
    return {"tema": "Jazz", "tempo_valor": 2, "tempo_unidade": "semanas"}


def test_plano_create_sem_contexto() -> None:
    plano = PlanoCreate.model_validate(_base_plano())
    assert plano.contexto is None


def test_plano_create_com_contexto_parcial() -> None:
    data = {**_base_plano(), "contexto": {"nivel": "basico"}}
    plano = PlanoCreate.model_validate(data)
    assert plano.contexto is not None
    assert plano.contexto.nivel == NivelConhecimento.basico
    assert plano.contexto.orcamento is None


def test_plano_create_com_contexto_completo() -> None:
    data = {
        **_base_plano(),
        "contexto": {
            "nivel": "intermediario",
            "orcamento": "gratuito",
            "idioma": "apenas_portugues",
            "rotina": "prefere_assistir",
            "localizacao": "Curitiba, PR",
            "motivacao": "hobby",
        },
    }
    plano = PlanoCreate.model_validate(data)
    assert plano.contexto is not None
    assert plano.contexto.tem_dados() is True
    assert plano.contexto.localizacao == "Curitiba, PR"


def test_plano_create_rejeita_contexto_com_localizacao_longa() -> None:
    data = {**_base_plano(), "contexto": {"localizacao": "x" * 101}}
    with pytest.raises(ValidationError):
        PlanoCreate.model_validate(data)


def test_plano_create_backward_compat() -> None:
    # Existing clients that don't send contexto must still work
    plano = PlanoCreate.model_validate(_base_plano())
    assert plano.tema == "Jazz"
    assert plano.tempo_valor == 2
    assert plano.contexto is None
