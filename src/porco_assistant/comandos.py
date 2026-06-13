"""Comandos de voz — parar, cancelar, novo assunto."""

from __future__ import annotations

import re

_PARAR = re.compile(
    r"^(?:parar?|pare|para|cancela(?:r|do|da)?|cancele|stop)"
    r"(?:\s+(?:o\s+)?agente)?[!.…]*$",
    re.I,
)
_NOVO = re.compile(
    r"^(?:novo\s+assunto|assunto\s+novo|mudar\s+assunto|outro\s+assunto)$",
    re.I,
)
_PARAR_PALAVRAS = frozenset(
    {
        "parar",
        "para",
        "pare",
        "stop",
        "cancelar",
        "cancela",
        "cancelado",
        "cancelada",
        "cancele",
    }
)


def eh_parar(texto: str) -> bool:
    t = re.sub(r"[^\w\s]", "", texto.strip().lower())
    if t in _PARAR_PALAVRAS:
        return True
    return bool(_PARAR.match(texto.strip()))


def eh_novo_assunto(texto: str) -> bool:
    return bool(_NOVO.match(texto.strip()))
