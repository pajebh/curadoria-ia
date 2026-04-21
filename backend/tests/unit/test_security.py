from uuid import uuid4

from app.core.security import create_session_token, decode_session_token, hash_token


def test_hash_token_deterministico() -> None:
    token = "meu-token-de-teste"
    assert hash_token(token) == hash_token(token)


def test_hash_diferente_para_tokens_diferentes() -> None:
    assert hash_token("token-a") != hash_token("token-b")


def test_create_e_decode_roundtrip() -> None:
    session_id = uuid4()
    token = create_session_token(session_id)
    decoded = decode_session_token(token)
    assert decoded == session_id


def test_decode_token_invalido() -> None:
    resultado = decode_session_token("token-invalido")
    assert resultado is None


def test_decode_token_vazio() -> None:
    resultado = decode_session_token("")
    assert resultado is None
