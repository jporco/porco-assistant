#!/usr/bin/env bash
set -euo pipefail
UIDN="$(id -u)"
PGID_FILE="/run/user/${UIDN}/porco-assistant-tts.pgid"

if [[ -f "$PGID_FILE" ]]; then
  PGID="$(tr -d ' \n' < "$PGID_FILE")"
  kill -9 -- "-${PGID}" 2>/dev/null || kill -9 "-${PGID}" 2>/dev/null || true
  rm -f "$PGID_FILE"
fi

pkill -9 -u "$USER" -f 'porco-assistant-tts' 2>/dev/null || true
rm -f "/run/user/${UIDN}/porco-assistant-tts.txt" 2>/dev/null || true

ROOT="${PORCO_ASSISTANT_HOME:?PORCO_ASSISTANT_HOME not set}"
export PYTHONPATH="${ROOT}/src"
"${ROOT}/.venv/bin/python" -c "from porco_assistant.voice.core.tts_piper import parar_agora; parar_agora()" 2>/dev/null || true
notify-send -a "Porco Assistant" -i "media-playback-stop" "Speech stopped" 2>/dev/null || true
