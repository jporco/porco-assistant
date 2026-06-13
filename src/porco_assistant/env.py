"""Carrega config.env."""

from __future__ import annotations

import os
from pathlib import Path


def carregar() -> None:
    base = Path(__file__).resolve().parents[2]
    for nome in ("config.env", "config.env.example"):
        arq = base / nome
        if not arq.is_file():
            continue
        for linha in arq.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave, valor = chave.strip(), valor.strip()
            if chave and (nome == "config.env" or chave not in os.environ):
                os.environ[chave] = valor
        break
