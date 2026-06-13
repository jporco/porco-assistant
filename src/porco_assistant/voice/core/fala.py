"""Limpa e resume texto para fala — sem markdown nem lixo."""

from __future__ import annotations

import json
import re

_RE_CODE = re.compile(r"```[\s\S]*?```|`[^`]+`")
_RE_MD = re.compile(r"[*_~#>|\\]")
_RE_URL = re.compile(r"https?://\S+|www\.\S+")
_RE_PATH = re.compile(
    r"(?:~/?|/(?:mnt|home|tmp|usr|var|opt|run)(?:/[\w.\-]+)+"
    r"|[A-Za-z]:\\[\w.\\\-]+)"
)
_RE_JSON_BLOCK = re.compile(r"\{[^{}]{2,}\}|\[[^\[\]]{2,}\]")
_RE_ESPACO = re.compile(r"\s+")
_RE_SO_LIXO = re.compile(r"^[\s.,;:!?…\-–—•·]+$")


def _so_lixo(texto: str) -> bool:
    t = texto.strip()
    if not t:
        return True
    if _RE_SO_LIXO.match(t):
        return True
    if len(t) < 3 and not re.search(r"[À-ÿA-Za-z]{2,}", t):
        return True
    return False


def _tentar_json(texto: str) -> str:
    t = texto.strip()
    if not t or t[0] not in "{[":
        return texto
    try:
        obj = json.loads(t)
    except json.JSONDecodeError:
        return texto
    if isinstance(obj, dict):
        for chave in ("message", "text", "content", "result", "summary"):
            val = obj.get(chave)
            if isinstance(val, str) and val.strip():
                return val
    if isinstance(obj, list):
        partes = [str(x) for x in obj if isinstance(x, str) and x.strip()]
        if partes:
            return " ".join(partes)
    return ""


def limpar_para_fala(texto: str) -> str:
    if not texto:
        return ""
    t = texto
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = _RE_CODE.sub(" ", t)
    t = _RE_JSON_BLOCK.sub(" ", t)
    t = _RE_URL.sub(" ", t)
    t = _RE_PATH.sub(" ", t)
    t = re.sub(r"^#{1,6}\s+", "", t, flags=re.M)
    t = _RE_MD.sub(" ", t)
    t = re.sub(r"\s*[-•]\s+", ". ", t)
    t = re.sub(r"\.{2,}", ".", t)
    t = _RE_ESPACO.sub(" ", t).strip(" .,;:-")
    if _so_lixo(t):
        return ""
    return t


def resumir_para_fala(texto: str, *, max_chars: int = 500, frases: int = 4) -> str:
    bruto = _tentar_json(texto)
    t = limpar_para_fala(bruto or texto)
    if not t:
        return ""
    partes = re.split(r"(?<=[.!?])\s+", t)
    saida: list[str] = []
    for p in partes:
        p = p.strip()
        if _so_lixo(p) or len(p) < 4:
            continue
        saida.append(p)
        if len(saida) >= frases:
            break
    res = " ".join(saida) if saida else t
    if len(res) <= max_chars:
        return res
    corte = res[:max_chars].rsplit(" ", 1)[0]
    return (corte or res[:max_chars]).rstrip(".,;:") + "."


def frase_curta(texto: str, max_chars: int = 120) -> str:
    return resumir_para_fala(texto, max_chars=max_chars, frases=2)
