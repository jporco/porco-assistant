#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${PORCO_ASSISTANT_HOME:-$REPO_ROOT}"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
SYSTEMD_USER="${HOME}/.config/systemd/user"

log() { printf '==> %s\n' "$*"; }

systemctl --user disable --now porco-assistant.service 2>/dev/null || true
rm -f "${SYSTEMD_USER}/porco-assistant.service"
systemctl --user daemon-reload 2>/dev/null || true

for name in \
  porco-assistant-open-agent.sh \
  porco-assistant-voice-on.sh \
  porco-assistant-voice-off.sh \
  porco-assistant-voice-stop.sh \
  porco-assistant-agent-tts-hook.sh
do
  rm -f "${BIN_DIR}/${name}"
done

for f in porco-assistant-voice-on.desktop \
         porco-assistant-voice-off.desktop \
         porco-assistant-voice-stop.desktop
do
  rm -f "${APP_DIR}/${f}"
done

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi

log "Removed service, menu shortcuts, and wrappers."
log "Project files kept at ${INSTALL_DIR} (remove manually if desired)."
