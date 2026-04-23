import re


class TemaInseguroError(ValueError):
    pass


class LocalizacaoInseguraError(ValueError):
    pass


PADROES_INJECTION = [
    r"ignore\s+(previous|all|above|instructions)",
    r"disregard\s+(previous|all|above|instructions)",
    r"system\s*:",
    r"<\/?(system|assistant|user)>",
    r"act\s+as\s+(?!a\s+student|an?\s+expert)",
    r"```\s*system",
    r"\[INST\]",
    r"\[\/INST\]",
    r"jailbreak",
    r"prompt\s+injection",
    r"you\s+are\s+now",
    r"forget\s+(everything|all|your)",
    r"new\s+persona",
    r"override\s+(your|all)\s+(instructions|rules)",
    r"do\s+anything\s+now",
    r"dan\s+mode",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in PADROES_INJECTION]


def validar_tema(tema: str) -> None:
    if len(tema) < 3:
        raise TemaInseguroError("Tema muito curto (mínimo 3 caracteres)")
    if len(tema) > 200:
        raise TemaInseguroError("Tema muito longo (máximo 200 caracteres)")

    for pattern in _compiled:
        if pattern.search(tema):
            raise TemaInseguroError(
                "O tema contém padrões não permitidos. "
                "Por favor, descreva o assunto que deseja aprender."
            )


def validar_localizacao(localizacao: str) -> None:
    if len(localizacao) > 100:
        raise LocalizacaoInseguraError("Localização muito longa (máximo 100 caracteres)")

    for pattern in _compiled:
        if pattern.search(localizacao):
            raise LocalizacaoInseguraError(
                "A localização contém padrões não permitidos. "
                "Por favor, informe apenas cidade e estado."
            )
