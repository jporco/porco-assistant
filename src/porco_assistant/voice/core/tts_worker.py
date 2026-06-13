"""Processo separado — sintetiza/fala sem bloquear o hook."""

from __future__ import annotations

import sys

from porco_assistant.voice.core.tts_piper import falar


def main() -> int:
    texto = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    if texto.strip():
        falar(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
