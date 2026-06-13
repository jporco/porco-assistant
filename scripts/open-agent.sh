#!/usr/bin/env bash
# Sends voice prompts to Cursor Agents via xdotool (X11).
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
export QT_QPA_PLATFORM=xcb

CURSOR="/usr/share/cursor/cursor"
[[ -x "${CURSOR}" ]] || CURSOR="${HOME}/.local/bin/cursor"
LOG="/tmp/porco-assistant-agent.log"
LAST_AGENT="/run/user/$(id -u)/porco-assistant.last-agent"
XDO=/usr/bin/xdotool

cursor_running() {
  pgrep -f '/usr/share/cursor/resources/app/cursor.mjs' >/dev/null 2>&1
}

find_agents_window() {
  local wid title
  for wid in $($XDO search --classname cursor 2>/dev/null); do
    title="$($XDO getwindowname "$wid" 2>/dev/null || true)"
    if [[ "${title}" == *"Agents"* || "${title}" == *"Chat"* ]]; then
      echo "$wid"
      return 0
    fi
  done
  return 1
}

janela_valida() {
  local wid="$1"
  [[ -n "${wid}" && "${wid}" != "0" ]] || return 1
  $XDO getwindowname "${wid}" >/dev/null 2>&1
}

ultimo_agente() {
  local wid
  [[ -f "${LAST_AGENT}" ]] || return 1
  wid="$(tr -d '[:space:]' < "${LAST_AGENT}")"
  janela_valida "${wid}" || return 1
  echo "${wid}"
}

salvar_agente() {
  local wid="$1"
  [[ -n "${wid}" ]] || return 0
  mkdir -p "$(dirname "${LAST_AGENT}")"
  echo "${wid}" > "${LAST_AGENT}"
}

abrir_agents() {
  [[ -x "${CURSOR}" ]] || return 1
  if cursor_running; then
    "${CURSOR}" --suppress-popups-on-startup --reuse-window --chat >/dev/null 2>&1 &
  else
    setsid -f "${CURSOR}" --suppress-popups-on-startup --chat >/dev/null 2>&1 \
      || "${CURSOR}" --suppress-popups-on-startup --chat >/dev/null 2>&1 &
  fi
  local i max_wait
  max_wait="${ASSISTANT_CURSOR_WAIT_LOOPS:-120}"
  for i in $(seq 1 "${max_wait}"); do
    sleep 0.25
    find_agents_window && return 0
  done
  return 1
}

restaurar_foco() {
  local prev="${1:-}"
  [[ -n "${prev}" && "${prev}" != "0" ]] || return 0
  $XDO windowactivate "${prev}" 2>/dev/null || true
}

focar_agents() {
  local WID="$1"
  $XDO windowactivate "${WID}" 2>/dev/null || true
  $XDO windowfocus "${WID}" 2>/dev/null || true
  sleep 0.25
}

{
  MODO="${2:-continuar}"
  PROMPT_FILE="${1:-}"
  PREV="$($XDO getactivewindow 2>/dev/null || echo 0)"
  echo "[$(date '+%F %T')] modo=${MODO} prev=${PREV}"

  if [[ "${MODO}" == "parar" ]]; then
    WID="$(find_agents_window || true)"
    if [[ -n "${WID}" ]]; then
      $XDO key --window "${WID}" --clearmodifiers Escape
      sleep 0.08
      $XDO key --window "${WID}" --clearmodifiers Escape
    fi
    restaurar_foco "${PREV}"
    exit 0
  fi

  WID="$(find_agents_window || true)"
  if [[ "${MODO}" == "continuar" ]]; then
    ULT="$(ultimo_agente || true)"
    if [[ -n "${ULT}" ]]; then
      WID="${ULT}"
    fi
  fi
  if [[ -z "${WID}" ]]; then
    abrir_agents || true
    WID="$(find_agents_window || true)"
  fi
  if [[ -z "${WID}" ]]; then
    echo "Agents window not found"
    exit 1
  fi

  focar_agents "${WID}"

  if [[ "${MODO}" == "novo_chat" ]]; then
    $XDO key --window "${WID}" --clearmodifiers ctrl+n
    sleep 1.0
    salvar_agente "${WID}"
    restaurar_foco "${PREV}"
    exit 0
  fi

  if [[ -z "${PROMPT_FILE}" || ! -f "${PROMPT_FILE}" ]]; then
    exit 1
  fi

  TEXTO="$(tr '\n' ' ' < "${PROMPT_FILE}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  if [[ -z "${TEXTO}" ]]; then
    exit 1
  fi

  if [[ "${MODO}" == "novo_enviar" ]]; then
    $XDO key --window "${WID}" --clearmodifiers ctrl+n
    sleep 1.2
  fi

  if command -v xclip >/dev/null 2>&1; then
    printf '%s' "${TEXTO}" | xclip -selection clipboard
    $XDO key --window "${WID}" --clearmodifiers ctrl+v
    sleep 0.15
    $XDO key --window "${WID}" --clearmodifiers Return
  else
    $XDO type --window "${WID}" --delay 1 --clearmodifiers "${TEXTO:0:2000}"
    $XDO key --window "${WID}" --clearmodifiers Return
  fi

  salvar_agente "${WID}"
  sleep 0.12
  restaurar_foco "${PREV}"
} >> "${LOG}" 2>&1
