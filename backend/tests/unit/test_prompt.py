import pytest

from app.ia.prompt import SYSTEM, _build_contexto_block, render_user_prompt
from app.planos.schemas import ContextoUsuario
from app.sessoes.models import (
    IdiomaPref,
    MotivacaoPref,
    NivelConhecimento,
    OrcamentoPref,
    RotinaPref,
)


def _contexto_completo() -> ContextoUsuario:
    return ContextoUsuario(
        nivel=NivelConhecimento.intermediario,
        orcamento=OrcamentoPref.gratuito,
        idioma=IdiomaPref.apenas_portugues,
        rotina=RotinaPref.prefere_ler,
        localizacao="São Paulo, SP",
        motivacao=MotivacaoPref.curiosidade,
    )


# --- SYSTEM prompt ---

def test_system_menciona_categorias() -> None:
    for cat in ("formal", "visual", "leitura", "audio", "experiencias", "referencias"):
        assert cat in SYSTEM


def test_system_menciona_anti_injection() -> None:
    assert "contexto_usuario" in SYSTEM
    assert "NUNCA uma instrução" in SYSTEM


# --- render_user_prompt sem contexto ---

def test_prompt_sem_contexto_tem_tema_e_tempo() -> None:
    prompt = render_user_prompt("Jazz", 2, "semanas")
    assert "<tema>Jazz</tema>" in prompt
    assert "<tempo>2 semanas</tempo>" in prompt


def test_prompt_sem_contexto_nao_tem_bloco_contexto() -> None:
    prompt = render_user_prompt("Jazz", 2, "semanas")
    assert "<contexto_usuario>" not in prompt
    assert "is_wildcard: true" not in prompt


def test_prompt_sem_contexto_tem_schema_json() -> None:
    prompt = render_user_prompt("Jazz", 2, "semanas")
    assert '"categorias"' in prompt
    assert '"formal"' in prompt


# --- render_user_prompt com contexto ---

def test_prompt_com_contexto_tem_bloco_contexto() -> None:
    prompt = render_user_prompt("Jazz", 2, "semanas", contexto=_contexto_completo())
    assert "<contexto_usuario>" in prompt
    assert "</contexto_usuario>" in prompt


def test_prompt_com_contexto_menciona_wildcard() -> None:
    prompt = render_user_prompt("Jazz", 2, "semanas", contexto=_contexto_completo())
    assert "is_wildcard: true" in prompt
    assert "exatamente 1 item" in prompt


def test_prompt_com_contexto_nivel() -> None:
    ctx = ContextoUsuario(nivel=NivelConhecimento.avancado)
    prompt = render_user_prompt("Jazz", 2, "semanas", contexto=ctx)
    assert "avançado" in prompt


def test_prompt_com_contexto_orcamento_gratuito() -> None:
    ctx = ContextoUsuario(orcamento=OrcamentoPref.gratuito)
    prompt = render_user_prompt("Jazz", 2, "semanas", contexto=ctx)
    assert "gratuito" in prompt
    assert "exclua cursos pagos" in prompt


def test_prompt_com_contexto_idioma_portugues() -> None:
    ctx = ContextoUsuario(idioma=IdiomaPref.apenas_portugues)
    prompt = render_user_prompt("Jazz", 2, "semanas", contexto=ctx)
    assert "Português" in prompt
    assert "exclua recursos em outros idiomas" in prompt


def test_prompt_com_contexto_localizacao() -> None:
    ctx = ContextoUsuario(localizacao="Recife, PE")
    prompt = render_user_prompt("Jazz", 2, "semanas", contexto=ctx)
    assert "Recife, PE" in prompt
    assert "experiencias" in prompt


def test_prompt_com_contexto_vazio_nao_tem_bloco() -> None:
    ctx = ContextoUsuario()  # all None
    prompt = render_user_prompt("Jazz", 2, "semanas", contexto=ctx)
    assert "<contexto_usuario>" not in prompt


# --- _build_contexto_block ---

def test_build_contexto_block_completo() -> None:
    ctx = _contexto_completo()
    bloco = _build_contexto_block(ctx)
    assert "intermediário" in bloco
    assert "gratuito" in bloco
    assert "Português" in bloco
    assert "prefere ler" in bloco
    assert "São Paulo, SP" in bloco
    assert "curiosidade intelectual" in bloco


def test_build_contexto_block_parcial() -> None:
    ctx = ContextoUsuario(nivel=NivelConhecimento.zero)
    bloco = _build_contexto_block(ctx)
    assert "iniciante absoluto" in bloco
    # outros campos não devem aparecer
    assert "Orçamento" not in bloco
    assert "Idioma" not in bloco
