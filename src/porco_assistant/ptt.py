"""Grava frase após Meta+Z."""

from __future__ import annotations

import logging
import os
import queue
import struct
import threading
import time

import numpy as np
import sounddevice as sd

from porco_assistant import mic, stt

logger = logging.getLogger("jarvis.ptt")

RATE = 16000


def _rms(chunk: bytes) -> float:
    n = len(chunk) // 2
    if not n:
        return 0.0
    s = struct.unpack(f"{n}h", chunk)
    return (sum(x * x for x in s) / n) ** 0.5


def _mono(raw: bytes, ch: int, cap_rate: int, gain: float) -> bytes:
    a = np.frombuffer(raw, dtype=np.int16)
    m = a.reshape(-1, ch).mean(axis=1).astype(np.int16) if ch >= 2 else a
    if cap_rate != RATE:
        n = max(1, int(len(m) * RATE / cap_rate))
        m = np.interp(
            np.linspace(0, 1, n, endpoint=False),
            np.linspace(0, 1, len(m), endpoint=False),
            m.astype(np.float32),
        ).astype(np.int16)
    if gain != 1.0:
        m = np.clip(m.astype(np.float32) * gain, -32768, 32767).astype(np.int16)
    return m.tobytes()


def _esvaziar(q: queue.Queue[bytes], segundos: float) -> None:
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        try:
            q.get_nowait()
        except queue.Empty:
            time.sleep(0.02)


def gravar() -> str:
    rms_min = int(os.environ.get("STT_RMS", "4"))
    gain = float(os.environ.get("STT_GAIN", "3.5"))
    sil = float(os.environ.get("STT_SILENCE_S", "0.45"))
    max_s = float(os.environ.get("STT_MAX_S", "8"))
    espera = float(os.environ.get("PTT_ESPERA_S", "4"))

    dev = mic.resolver()
    mic.ativar()
    info = sd.query_devices(dev) if dev is not None else {}
    cap_rate = int(info.get("default_samplerate") or RATE)
    ch = min(2, max(1, int(info.get("max_input_channels") or 1)))
    block = int(cap_rate * 0.05)
    max_bytes = int(RATE * max_s * 2)

    q: queue.Queue[bytes] = queue.Queue(maxsize=64)
    pronto = threading.Event()
    saida: list[str] = [""]

    def cb(indata, frames, time_info, status) -> None:
        try:
            q.put_nowait(bytes(indata))
        except queue.Full:
            try:
                q.get_nowait()
                q.put_nowait(bytes(indata))
            except queue.Empty:
                pass

    def processar() -> None:
        _esvaziar(q, 0.15)
        buf = bytearray()
        falando = False
        sil_desde = 0.0
        t0 = time.monotonic()
        pico_rms = 0.0
        while not pronto.is_set():
            try:
                raw = q.get(timeout=0.2)
            except queue.Empty:
                now = time.monotonic()
                if falando and sil_desde and now - sil_desde >= sil:
                    break
                if not falando and now - t0 >= espera:
                    logger.info("Timeout sem fala (limiar RMS=%d)", rms_min)
                    return
                continue
            chunk = _mono(raw, ch, cap_rate, gain)
            nivel = _rms(chunk)
            pico_rms = max(pico_rms, nivel)
            now = time.monotonic()
            if nivel >= rms_min:
                falando = True
                sil_desde = 0.0
                buf.extend(chunk)
                if len(buf) >= max_bytes:
                    break
            elif falando:
                if not sil_desde:
                    sil_desde = now
                buf.extend(chunk)
                if now - sil_desde >= sil:
                    break
        pcm = bytes(buf)
        dur = len(pcm) / (RATE * 2)
        min_s = float(os.environ.get("STT_MIN_S", "1.0"))
        logger.info("Gravou %.1fs RMS_pico=%.0f", dur, pico_rms)
        if dur < min_s:
            logger.info("Gravação curta demais (<%.1fs)", min_s)
            return
        if len(pcm) >= RATE // 4:
            txt = stt.transcrever(pcm)
            if txt and stt.aceitavel(txt):
                saida[0] = txt

    worker = threading.Thread(target=processar, daemon=True)
    with sd.RawInputStream(
        samplerate=cap_rate,
        blocksize=block,
        dtype="int16",
        channels=ch,
        device=dev,
        callback=cb,
    ):
        worker.start()
        worker.join(timeout=max_s + espera + 2)
    pronto.set()
    worker.join(timeout=1)
    if saida[0]:
        logger.info("Ouviu: %s", saida[0])
    return saida[0]
