#!/usr/bin/env bash
set -euo pipefail
ROOT="${PORCO_ASSISTANT_HOME:?PORCO_ASSISTANT_HOME not set}"
export PYTHONPATH="${ROOT}/src"
"${ROOT}/.venv/bin/python" -c "from porco_assistant.voice.core.voz import definir_voz; definir_voz(False)"
notify-send -a "Porco Assistant" -i "audio-volume-muted" \
  "Agent voice off" "Agent replies will not be read aloud."
