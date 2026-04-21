import time

import pytest

from app.ia.orchestrator import CircuitBreaker


def test_inicia_fechado() -> None:
    cb = CircuitBreaker()
    assert not cb.is_open()


def test_abre_apos_threshold() -> None:
    cb = CircuitBreaker(failure_threshold=5, timeout=60)
    for _ in range(5):
        cb.record_failure()
    assert cb.is_open()


def test_nao_abre_antes_threshold() -> None:
    cb = CircuitBreaker(failure_threshold=5, timeout=60)
    for _ in range(4):
        cb.record_failure()
    assert not cb.is_open()


def test_reset_fecha_circuit() -> None:
    cb = CircuitBreaker(failure_threshold=3, timeout=60)
    for _ in range(3):
        cb.record_failure()
    assert cb.is_open()
    cb.reset()
    assert not cb.is_open()


def test_fecha_apos_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    cb = CircuitBreaker(failure_threshold=3, timeout=10)
    for _ in range(3):
        cb.record_failure()
    assert cb.is_open()

    # simula passagem de tempo
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 11)
    assert not cb.is_open()
