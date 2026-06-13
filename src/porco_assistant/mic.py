"""Microphone selection and PulseAudio/PipeWire setup."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger("assistant.mic")


def _hint() -> str:
    return os.environ.get("MIC_DEVICE", "default").strip().lower()


def _combina(nome: str, hint: str) -> bool:
    n = nome.lower()
    if hint in ("", "default"):
        return "monitor" not in n
    if hint.isdigit():
        return False
    return hint in n


def ativar() -> None:
    hint = _hint()
    if hint in ("", "default") or hint.isdigit():
        return
    try:
        r = subprocess.run(
            ["pactl", "list", "sources", "short"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        for linha in (r.stdout or "").splitlines():
            partes = linha.split()
            if len(partes) < 2:
                continue
            nome = " ".join(partes[1:])
            if not _combina(nome, hint):
                continue
            idx = partes[0]
            subprocess.run(
                ["pactl", "suspend-source", idx, "0"], timeout=2, check=False
            )
            subprocess.run(
                ["pactl", "set-source-mute", idx, "0"], timeout=2, check=False
            )
            vol = os.environ.get("MIC_VOLUME", "120%").strip()
            if vol:
                subprocess.run(
                    ["pactl", "set-source-volume", idx, vol],
                    timeout=2,
                    check=False,
                )
            return
    except (OSError, subprocess.SubprocessError):
        pass


def resolver() -> Optional[int]:
    import sounddevice as sd

    hint = _hint()
    if hint.isdigit():
        return int(hint)

    fallback: tuple[int, str] | None = None
    for i, dev in enumerate(sd.query_devices()):
        if int(dev.get("max_input_channels") or 0) < 1:
            continue
        nome = str(dev.get("name", ""))
        if hint not in ("", "default") and _combina(nome, hint):
            logger.info("Mic [%d] %s", i, nome)
            return i
        if fallback is None and "monitor" not in nome.lower():
            fallback = (i, nome)

    if fallback:
        logger.info("Mic padrão [%d] %s", fallback[0], fallback[1])
        return fallback[0]
    return None
