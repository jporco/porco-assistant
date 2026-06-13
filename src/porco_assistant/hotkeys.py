"""Atalhos Meta+Z / Ctrl+Meta+Z — evdev em todos os nós do teclado."""

from __future__ import annotations

import logging
import os
import select
import subprocess
import time
from pathlib import Path

logger = logging.getLogger("jarvis.hotkeys")

_TRIGGER = Path(f"/run/user/{os.getuid()}/porco-assistant.wake")
_ULTIMO = 0.0


def _abrir_dispositivos():
    import evdev
    from evdev import ecodes

    out = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            if "mouse" in dev.name.lower():
                continue
            keys = dev.capabilities().get(ecodes.EV_KEY, [])
            if ecodes.KEY_Z not in keys:
                continue
            if ecodes.KEY_LEFTMETA not in keys and ecodes.KEY_RIGHTMETA not in keys:
                continue
            out.append(dev)
        except (OSError, PermissionError):
            continue
    return out


def _acordar(modo: str) -> None:
    global _ULTIMO
    agora = time.monotonic()
    if agora - _ULTIMO < 1.5:
        return
    _ULTIMO = agora
    _TRIGGER.parent.mkdir(parents=True, exist_ok=True)
    _TRIGGER.write_text(modo, encoding="utf-8")
    label = "Ctrl+Meta+Z" if modo == "continuar" else "Meta+Z"
    logger.info("%s → %s", label, modo)


def _fechar(devices) -> None:
    for dev in devices or []:
        try:
            dev.close()
        except OSError:
            pass


def monitor() -> None:
    if os.environ.get("ASSISTANT_HOTKEYS", "1") != "1":
        return
    try:
        import evdev
        from evdev import ecodes
    except ImportError:
        logger.warning("evdev não instalado")
        return

    meta = False
    ctrl = False
    devices = []
    fds: dict = {}
    _ultimo_stop = 0.0

    def _parar_voz() -> None:
        nonlocal _ultimo_stop
        agora = time.monotonic()
        if agora - _ultimo_stop < 0.25:
            return
        _ultimo_stop = agora
        try:
            from porco_assistant.voice.core.tts_piper import parar_agora

            parar_agora()
            logger.info("Ctrl+Meta+A → parar TTS")
        except Exception:
            subprocess.run(
                [os.path.expanduser("~/.local/bin/porco-assistant-voice-stop.sh")],
                check=False,
            )

    while True:
        if not fds:
            _fechar(devices)
            devices = _abrir_dispositivos()
            if not devices:
                logger.warning("Nenhum teclado Meta+Z")
                time.sleep(5)
                continue
            for dev in devices:
                logger.info("Hotkeys: [%s] %s", dev.path, dev.name)
            fds = {d.fd: d for d in devices}

        try:
            ready, _, _ = select.select(list(fds.keys()), [], [], 1.0)
        except (OSError, ValueError):
            fds = {}
            time.sleep(1)
            continue

        for fd in ready:
            dev = fds[fd]
            try:
                events = dev.read()
            except OSError:
                fds = {}
                break
            for event in events:
                if event.type != ecodes.EV_KEY:
                    continue
                code, val = event.code, event.value
                if code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
                    if val in (0, 1):
                        meta = val == 1
                elif code in (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL):
                    if val in (0, 1):
                        ctrl = val == 1
                elif code == ecodes.KEY_Z and val == 1:
                    try:
                        active = dev.active_keys()
                    except OSError:
                        active = []
                    meta_on = meta or ecodes.KEY_LEFTMETA in active or ecodes.KEY_RIGHTMETA in active
                    if not meta_on:
                        continue
                    ctrl_on = (
                        ctrl
                        or ecodes.KEY_LEFTCTRL in active
                        or ecodes.KEY_RIGHTCTRL in active
                    )
                    _acordar("continuar" if ctrl_on else "novo")
                elif code == ecodes.KEY_A and val == 1:
                    try:
                        active = dev.active_keys()
                    except OSError:
                        active = []
                    meta_on = meta or ecodes.KEY_LEFTMETA in active or ecodes.KEY_RIGHTMETA in active
                    if not meta_on:
                        continue
                    ctrl_on = (
                        ctrl
                        or ecodes.KEY_LEFTCTRL in active
                        or ecodes.KEY_RIGHTCTRL in active
                    )
                    if ctrl_on:
                        _parar_voz()
