"""Texto → áudio via Piper cadu — mesmo pipeline do piper_read.sh."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

from porco_assistant.voice.core.audio_out import parar_som, tocar_pipeline
from porco_assistant.voice.core.fala import resumir_para_fala

logger = logging.getLogger("jarvis.tts")

_LOCK = threading.Lock()
_MAX_CHARS = int(os.environ.get("AGENT_TTS_MAX_CHARS", "600"))
_ROOT = Path(__file__).resolve().parents[4]


def _cfg() -> dict[str, str | float | Path]:
    home = Path.home()
    return {
        "piper": Path(os.environ.get("PIPER_BIN", "/usr/bin/piper-tts")),
        "modelo": Path(
            os.environ.get(
                "PIPER_MODEL",
                str(home / ".config/piper/pt-BR-cadu-medium.onnx"),
            )
        ),
        "rate": int(os.environ.get("PIPER_RATE", "22050")),
        "speed": float(os.environ.get("PIPER_SPEED", "1.6")),
        "pitch": float(os.environ.get("PIPER_PITCH", "0.88")),
        "volume": float(os.environ.get("PIPER_VOLUME", "1.0")),
        "player": os.environ.get("PIPER_PLAYER", "aplay"),
        "ffmpeg": Path(os.environ.get("FFMPEG_BIN", "/usr/bin/ffmpeg")),
    }


def _filtro_ffmpeg(cfg: dict) -> str:
    rate = cfg["rate"]
    speed = cfg["speed"]
    pitch = cfg["pitch"]
    volume = cfg["volume"]
    return (
        f"asetrate={rate}*{pitch},atempo={speed},"
        f"highpass=f=200,"
        f"equalizer=f=4000:t=q:w=1:g=5,"
        f"equalizer=f=8000:t=q:w=1:g=3,"
        f"volume={volume}"
    )


def _python() -> Path:
    venv = _ROOT / ".venv" / "bin" / "python"
    return venv if venv.is_file() else Path(sys.executable)


def parar_agora() -> None:
    """Só corta o som — modo voz agente continua ativo."""
    parar_som()


def interromper() -> None:
    parar_agora()


def falar(texto: str) -> None:
    limpo = resumir_para_fala(texto, max_chars=_MAX_CHARS, frases=6)
    if not limpo:
        return

    with _LOCK:
        parar_som()
        try:
            _sintetizar(limpo)
        except Exception:
            logger.exception("TTS falhou")


def falar_em_background(texto: str) -> None:
    """Hook dispara worker separado — stop não quebra próximas leituras."""
    limpo = resumir_para_fala(texto, max_chars=_MAX_CHARS, frases=6)
    if not limpo:
        return
    parar_som()
    py = _python()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_ROOT / "src")
    subprocess.Popen(
        [str(py), "-m", "porco_assistant.voice.core.tts_worker", limpo],
        env=env,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _sintetizar(texto: str) -> None:
    cfg = _cfg()
    if not cfg["piper"].is_file() or not cfg["modelo"].is_file():
        logger.error("Piper ou modelo cadu ausente")
        return

    tmp = Path(f"/run/user/{os.getuid()}/porco-assistant-tts.txt")
    tmp.write_text(texto, encoding="utf-8")

    filtro = _filtro_ffmpeg(cfg)
    rate = cfg["rate"]
    bash = (
        f'cat "$1" | "{cfg["piper"]}" --model "{cfg["modelo"]}" --output_raw | '
        f'"{cfg["ffmpeg"]}" -f s16le -ar {rate} -ac 1 -i - -af "{filtro}" -f wav - | '
        f'"{cfg["player"]}" -q'
    )
    try:
        tocar_pipeline(["bash", "-c", bash, "porco-assistant-tts", str(tmp)])
    finally:
        tmp.unlink(missing_ok=True)
