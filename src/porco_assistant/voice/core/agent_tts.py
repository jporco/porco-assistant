"""Entrada do hook afterAgentResponse — fala respostas dos agentes."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from porco_assistant.voice.core.fala import limpar_para_fala
from porco_assistant.voice.core.tts_piper import falar_em_background
from porco_assistant.voice.core.voz import voz_ativa

logger = logging.getLogger("jarvis.agent_tts")

_CAMPOS = (
    "text",
    "agent_message",
    "response",
    "message",
    "content",
    "assistant_message",
    "body",
    "output",
)


def _extrair_texto(data: dict[str, Any]) -> str:
    for chave in _CAMPOS:
        val = data.get(chave)
        if isinstance(val, str) and val.strip():
            return val
    msg = data.get("message")
    if isinstance(msg, dict):
        for chave in _CAMPOS:
            val = msg.get(chave)
            if isinstance(val, str) and val.strip():
                return val
    for chave in ("messages", "blocks", "parts"):
        blocos = data.get(chave)
        if not isinstance(blocos, list):
            continue
        partes: list[str] = []
        for item in blocos:
            if isinstance(item, str) and item.strip():
                partes.append(item)
            elif isinstance(item, dict):
                for sub in _CAMPOS:
                    val = item.get(sub)
                    if isinstance(val, str) and val.strip():
                        partes.append(val)
        if partes:
            return "\n".join(partes)
    return ""


def processar_payload(data: dict[str, Any]) -> None:
    if not voz_ativa():
        return
    bruto = _extrair_texto(data)
    if not bruto:
        return
    limpo = limpar_para_fala(bruto)
    if not limpo or len(limpo) < 8:
        return
    falar_em_background(limpo)


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.debug("hook sem JSON válido")
        return 0
    if not isinstance(data, dict):
        return 0
    try:
        processar_payload(data)
    except Exception:
        logger.exception("agent TTS falhou")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
