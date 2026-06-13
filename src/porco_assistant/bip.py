"""Bip curto."""

from __future__ import annotations

import logging
import math
import os
import struct
import subprocess
import tempfile
import threading
import wave

logger = logging.getLogger("jarvis.bip")


def _tocar(path: str) -> bool:
    env = {
        **os.environ,
        "XDG_RUNTIME_DIR": f"/run/user/{os.getuid()}",
        "PULSE_SERVER": f"unix:/run/user/{os.getuid()}/pulse/native",
    }
    for cmd in (["paplay", path], ["pw-play", path], ["aplay", "-q", path]):
        try:
            if subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, timeout=2).returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            continue
    logger.warning("Bip: nenhum player de áudio respondeu")
    return False


def _gerar(freq: float, ms: int, vol: float) -> str:
    rate = 22050
    n = max(1, int(rate * ms / 1000))
    data = struct.pack(
        f"<{n}h",
        *(
            int(32767 * vol * math.sin(2 * math.pi * freq * i / rate))
            for i in range(n)
        ),
    )
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data)
    tmp.close()
    return tmp.name


def ouvir() -> None:
    """Bip ao apertar Meta+Z — curto, um tom."""
    freq = float(os.environ.get("BIP_FREQ", "900"))
    ms = int(os.environ.get("BIP_MS", "50"))
    vol = float(os.environ.get("BIP_VOL", "0.7"))
    path = _gerar(freq, ms, vol)
    try:
        _tocar(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def ouvir_async() -> None:
    threading.Thread(target=ouvir, daemon=True, name="Bip").start()
