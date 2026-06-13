"""Toggle e parada da leitura de respostas dos agentes Cursor."""

from __future__ import annotations

import os
from pathlib import Path

from porco_assistant.voice.core.tts_piper import parar_agora

# Persiste até clicar em Desativar (menu ou script off).
_FLAG = Path.home() / ".config" / "porco-assistant" / "agent-tts-on"
_RUN_FLAG = Path(f"/run/user/{os.getuid()}/porco-assistant-agent-tts")


def voz_ativa() -> bool:
    if _FLAG.is_file():
        return True
    # Migra flag antiga de sessão (/run) se existir.
    if _RUN_FLAG.is_file():
        definir_voz(True)
        _RUN_FLAG.unlink(missing_ok=True)
        return True
    return False


def definir_voz(ativo: bool) -> None:
    if ativo:
        _FLAG.parent.mkdir(parents=True, exist_ok=True)
        _FLAG.write_text("1\n", encoding="utf-8")
    else:
        _FLAG.unlink(missing_ok=True)
        _RUN_FLAG.unlink(missing_ok=True)
        parar_fala()


def parar_fala() -> None:
    """Corta o som atual. Não desativa o modo voz agente."""
    parar_agora()
