#!/usr/bin/env bash
set -euo pipefail
ROOT="${PORCO_ASSISTANT_HOME:?PORCO_ASSISTANT_HOME not set}"
export PYTHONPATH="${ROOT}/src"
exec "${ROOT}/.venv/bin/python" -m porco_assistant.voice.core.agent_tts
