"""Saída de áudio — parada imediata só do TTS do agente."""

from __future__ import annotations

import logging
import os
import signal
import subprocess
from pathlib import Path

logger = logging.getLogger("jarvis.audio")

_PIPELINE_MARK = "porco-assistant-tts"


def _uid() -> int:
    return os.getuid()


def _pgid_file() -> Path:
    return Path(f"/run/user/{_uid()}/porco-assistant-tts.pgid")


def _env_audio() -> dict[str, str]:
    env = dict(os.environ)
    uid = _uid()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    env.setdefault("PULSE_RUNTIME", f"/run/user/{uid}/pulse")
    env.setdefault("DISPLAY", ":0")
    return env


def registrar_pgid(proc: subprocess.Popen[bytes]) -> None:
    try:
        pgid = os.getpgid(proc.pid)
        _pgid_file().write_text(str(pgid), encoding="utf-8")
    except OSError:
        pass


def limpar_pgid() -> None:
    _pgid_file().unlink(missing_ok=True)


def parar_som() -> None:
    """Corta o áudio agora. Não desliga o modo voz agente."""
    pf = _pgid_file()
    if pf.is_file():
        try:
            pgid = int(pf.read_text(encoding="utf-8").strip())
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, OSError, ValueError):
            pass
        pf.unlink(missing_ok=True)

    uid = str(_uid())
    # Só pipeline do agente — não mata Meta+S / piper_read genérico.
    alvos = (
        ["pkill", "-9", "-u", uid, "-f", _PIPELINE_MARK],
    )
    for cmd in alvos:
        try:
            subprocess.run(cmd, capture_output=True, timeout=1, check=False)
        except (OSError, subprocess.SubprocessError):
            pass

    Path(f"/run/user/{_uid()}/porco-assistant-tts.txt").unlink(missing_ok=True)


def tocar_pipeline(cmd: list[str]) -> int:
    proc = subprocess.Popen(
        cmd,
        start_new_session=True,
        env=_env_audio(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    registrar_pgid(proc)
    try:
        return proc.wait()
    finally:
        limpar_pgid()
