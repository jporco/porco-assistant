"""Meta+Z → novo agente | Ctrl+Meta+Z → continuar."""

from __future__ import annotations

import logging
import os
import signal
import threading
import time
from pathlib import Path

from porco_assistant import agent, auth, bip, cursor_bg, hotkeys, mic, ptt, stt

logger = logging.getLogger("jarvis")
_TRIGGER = Path(f"/run/user/{os.getuid()}/porco-assistant.wake")


class Daemon:
    def __init__(self) -> None:
        self._on = True
        self._gravando = False
        self._lock = threading.Lock()
        self._ultimo_wake = 0.0

    def _ler_modo(self) -> str:
        try:
            modo = _TRIGGER.read_text(encoding="utf-8").strip().lower()
        except OSError:
            return "novo"
        return modo if modo in ("novo", "continuar") else "novo"

    def _ciclo(self, modo: str) -> None:
        with self._lock:
            if self._gravando:
                bip.ouvir()
                logger.info("Ocupado — aguarde terminar")
                return
            self._gravando = True
        try:
            bip.ouvir()
            delay_ms = float(os.environ.get("PTT_POST_BIP_MS", "400"))
            time.sleep(delay_ms / 1000.0)
            texto = ptt.gravar()
        except Exception:
            logger.exception("ciclo falhou")
            with self._lock:
                self._gravando = False
            return

        with self._lock:
            self._gravando = False

        try:
            if texto:
                agent.executar(texto, modo=modo)
            else:
                logger.info("Nada ouvido ou rejeitado")
        except Exception:
            logger.exception("agente falhou")

    def run(self) -> int:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )

        def _off(sig: int, _f: object) -> None:
            self._on = False

        signal.signal(signal.SIGTERM, _off)
        signal.signal(signal.SIGINT, _off)

        mic.ativar()
        auth.garantir()
        stt.warm()
        threading.Thread(
            target=cursor_bg.aquecer, daemon=True, name="CursorWarm"
        ).start()
        threading.Thread(
            target=hotkeys.monitor, daemon=True, name="Hotkeys"
        ).start()

        logger.info(
            "Pronto — Meta+Z (novo) | Ctrl+Meta+Z (continuar)"
        )
        while self._on:
            if _TRIGGER.exists():
                modo = self._ler_modo()
                _TRIGGER.unlink(missing_ok=True)
                agora = time.monotonic()
                if agora - self._ultimo_wake < 1.5:
                    continue
                self._ultimo_wake = agora
                label = "Ctrl+Meta+Z" if modo == "continuar" else "Meta+Z"
                logger.info("%s (modo=%s)", label, modo)
                threading.Thread(
                    target=self._ciclo,
                    args=(modo,),
                    daemon=True,
                    name="PTT",
                ).start()
            time.sleep(0.1)
        agent.parar()
        return 0
