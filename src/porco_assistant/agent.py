"""Meta+Z → fala → cola no agente Cursor (igual digitar + Enter)."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from porco_assistant import comandos, stt

logger = logging.getLogger("assistant.agent")

_SCRIPT = Path.home() / ".local/bin/porco-assistant-open-agent.sh"


def eh_parar(texto: str) -> bool:
    return comandos.eh_parar(texto)


def eh_novo_assunto(texto: str) -> bool:
    return comandos.eh_novo_assunto(texto)


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
        "XAUTHORITY": os.environ.get(
            "XAUTHORITY", str(Path.home() / ".Xauthority")
        ),
        "QT_QPA_PLATFORM": "xcb",
    }


def _run_script(*args: str, timeout: float | None = None) -> bool:
    if not _SCRIPT.is_file():
        logger.error("Script não encontrado: %s", _SCRIPT)
        return False
    limite = timeout or float(
        os.environ.get("ASSISTANT_UI_TIMEOUT_S", "45")
    )
    try:
        r = subprocess.run(
            [str(_SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=limite,
            env=_env(),
        )
        if r.returncode != 0:
            logger.warning(
                "UI rc=%s %s",
                r.returncode,
                (r.stderr or r.stdout or "")[:200],
            )
            return False
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("UI falhou: %s", exc)
        return False


def _modo_ui(modo: str) -> str:
    """novo → Ctrl+N + colar; continuar → mesma conversa."""
    return "continuar" if modo == "continuar" else "novo_enviar"


def _mandar_ui(texto: str, *, modo: str) -> bool:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    path = tmp.name
    ui_modo = _modo_ui(modo)
    timeout = float(os.environ.get("ASSISTANT_UI_TIMEOUT_S", "90"))
    try:
        tmp.write(texto.strip())
        tmp.close()
        ok = _run_script(path, ui_modo, timeout=timeout)
        if ok:
            logger.info("Enviado (%s): %s", ui_modo, texto[:100])
        return ok
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def parar() -> None:
    _run_script("/dev/null", "parar")
    logger.info("Parar")


def executar(texto: str, *, modo: str = "novo") -> None:
    t = texto.strip()
    if not t:
        return

    if eh_parar(t):
        parar()
        logger.info("Cancelado por voz")
        return
    if eh_novo_assunto(t):
        if _run_script("/dev/null", "novo_chat"):
            logger.info("Novo chat — próxima fala continua nele")
        return
    if not stt.aceitavel(t):
        logger.info("Ignorado: %s", t[:80])
        return

    _mandar_ui(t, modo=modo)
