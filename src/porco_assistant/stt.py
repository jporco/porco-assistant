"""STT — Whisper medium PT-BR."""

from __future__ import annotations

import logging
import os
import re
import threading

import numpy as np

logger = logging.getLogger("jarvis.stt")

RATE = 16000
_model = None
_lock = threading.Lock()

_PROMPT = ""

# Texto que o Whisper repete quando não ouve fala de verdade
_LIXO_PROMPT = re.compile(
    r"comando de voz|assistente do computador|portugu[eê]s do brasil",
    re.I,
)


def warm() -> None:
    _modelo()


def _modelo():
    global _model
    with _lock:
        if _model is not None:
            return _model
        from faster_whisper import WhisperModel

        nome = os.environ.get("WHISPER_MODEL", "medium")
        device = os.environ.get("WHISPER_DEVICE", "cuda")
        compute = os.environ.get("WHISPER_COMPUTE", "float32")
        if compute in ("int8_float16", "int8"):
            compute = "float32"
        logger.info("Whisper %s %s/%s", nome, device, compute)
        try:
            _model = WhisperModel(nome, device=device, compute_type=compute)
        except Exception as exc:
            if device == "cuda":
                logger.warning("CUDA float32 falhou (%s), tentando float16", exc)
                try:
                    _model = WhisperModel(nome, device="cuda", compute_type="float16")
                except Exception as exc2:
                    logger.warning("CUDA falhou (%s), CPU int8", exc2)
                    _model = WhisperModel(nome, device="cpu", compute_type="int8")
            else:
                logger.warning("CPU falhou (%s), int8", exc)
                _model = WhisperModel(nome, device="cpu", compute_type="int8")
        return _model


def eh_lixo(txt: str) -> bool:
    t = txt.strip()
    if not t:
        return True
    if _LIXO_PROMPT.search(t):
        return True
    if len(t) < 3:
        return True
    return False


def aceitavel(txt: str) -> bool:
    from porco_assistant import comandos

    t = txt.strip()
    if not t:
        return False
    if comandos.eh_parar(t) or comandos.eh_novo_assunto(t):
        return True
    return not eh_lixo(t)


def transcrever(pcm: bytes) -> str:
    if len(pcm) < RATE // 4:
        return ""
    arr = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    peak = float(np.max(np.abs(arr)))
    if peak > 1e-4:
        arr = arr * min(0.95 / peak, 4.0)

    model = _modelo()
    segs, _ = model.transcribe(
        arr,
        language="pt",
        beam_size=int(os.environ.get("WHISPER_BEAM", "5")),
        vad_filter=False,
        condition_on_previous_text=False,
        temperature=0.0,
        compression_ratio_threshold=2.4,
        log_prob_threshold=-1.0,
        no_speech_threshold=0.6,
    )
    txt = " ".join(s.text.strip() for s in segs if s.text.strip()).strip()
    if txt and eh_lixo(txt):
        logger.info("Descartado (lixo/prompt): %s", txt[:80])
        return ""
    if txt:
        logger.info("Transcreveu: %s", txt)
    return txt
