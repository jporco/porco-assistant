"""Mantém Cursor/Agents pronto em background — cold start evitado."""

from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path

logger = logging.getLogger("jarvis.cursor")

_CURSOR = Path("/usr/share/cursor/cursor")
_FALLBACK = Path.home() / ".local/bin/cursor"
_XDO = "/usr/bin/xdotool"


def _bin() -> Path | None:
    if _CURSOR.is_file():
        return _CURSOR
    if _FALLBACK.is_file():
        return _FALLBACK
    return None


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
        "XAUTHORITY": os.environ.get(
            "XAUTHORITY", str(Path.home() / ".Xauthority")
        ),
        "QT_QPA_PLATFORM": "xcb",
    }


def processo_rodando() -> bool:
    try:
        r = subprocess.run(
            ["pgrep", "-f", "/usr/share/cursor/resources/app/cursor.mjs"],
            capture_output=True,
            timeout=3,
            check=False,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def janela_agents() -> str | None:
    try:
        r = subprocess.run(
            [_XDO, "search", "--classname", "cursor"],
            capture_output=True,
            text=True,
            timeout=5,
            env=_env(),
            check=False,
        )
        for wid in (r.stdout or "").split():
            t = subprocess.run(
                [_XDO, "getwindowname", wid],
                capture_output=True,
                text=True,
                timeout=2,
                env=_env(),
                check=False,
            )
            title = (t.stdout or "").strip()
            if "Agents" in title or "Chat" in title:
                return wid
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _lançar(*, reuse: bool) -> None:
    binario = _bin()
    if not binario:
        logger.warning("Cursor não encontrado")
        return
    args = [str(binario), "--suppress-popups-on-startup"]
    if reuse:
        args.append("--reuse-window")
    args.append("--chat")
    try:
        subprocess.Popen(
            ["setsid", *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=_env(),
            start_new_session=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("Falha ao lançar Cursor: %s", exc)


def _esperar_agents(segundos: float) -> bool:
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        if janela_agents():
            return True
        time.sleep(0.25)
    return False


def aquecer() -> None:
    """Sobe Cursor cedo e deixa Agents pronto — sem roubar foco."""
    if os.environ.get("ASSISTANT_CURSOR_WARM", "1") != "1":
        return

    if janela_agents():
        logger.info("Agents já pronto")
        return

    if processo_rodando():
        logger.info("Cursor rodando — abrindo Agents (--reuse-window)")
        _lançar(reuse=True)
    else:
        logger.info("Cursor frio — aquecendo em background")
        _lançar(reuse=False)

    if _esperar_agents(float(os.environ.get("ASSISTANT_CURSOR_WARM_S", "45"))):
        logger.info("Agents pronto (warm)")
    else:
        logger.warning("Agents não ficou pronto a tempo no warm")


def garantir_agents_rapido() -> bool:
    """Chamado antes de colar — tenta reuse se processo já existe."""
    if janela_agents():
        return True
    if processo_rodando():
        _lançar(reuse=True)
    else:
        _lançar(reuse=False)
    return _esperar_agents(float(os.environ.get("ASSISTANT_CURSOR_WAIT_S", "20")))
