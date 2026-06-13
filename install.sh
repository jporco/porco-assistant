#!/usr/bin/env bash
# Porco Assistant — installer for Arch Linux and derivatives.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${PORCO_ASSISTANT_HOME:-$REPO_ROOT}"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
SYSTEMD_USER="${HOME}/.config/systemd/user"
MODELS_DIR="${INSTALL_DIR}/models"
PIPER_DIR="${INSTALL_DIR}/bin"
VENV="${INSTALL_DIR}/.venv"
PIPER_VER="1.2.0"
PIPER_URL="https://github.com/rhasspy/piper/releases/download/v${PIPER_VER}/piper_linux_x86_64.tar.gz"
VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/cadu/medium"

log() { printf '==> %s\n' "$*"; }
warn() { printf '!!> %s\n' "$*" >&2; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

arch_check() {
  if [[ -f /etc/arch-release ]] || command -v pacman >/dev/null 2>&1; then
    return 0
  fi
  die "This installer targets Arch Linux and derivatives (pacman required)."
}

install_packages() {
  local pkgs=(
    python
    python-pip
    ffmpeg
    alsa-utils
    xdotool
    xclip
    libnotify
    wget
    curl
  )
  log "Installing system packages (sudo may prompt)..."
  sudo pacman -S --needed --noconfirm "${pkgs[@]}"
}

setup_venv() {
  log "Python virtual environment at ${VENV}"
  if [[ ! -d "${VENV}" ]]; then
    python -m venv "${VENV}"
  fi
  "${VENV}/bin/pip" install --upgrade pip wheel
  "${VENV}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"
}

download_piper() {
  local piper_bin="${PIPER_DIR}/piper"
  if [[ -x "${piper_bin}" ]]; then
    log "Piper already present"
    return 0
  fi
  mkdir -p "${PIPER_DIR}"
  local tmp
  tmp="$(mktemp -d)"
  log "Downloading Piper ${PIPER_VER}..."
  curl -fsSL "${PIPER_URL}" | tar -xz -C "${tmp}"
  install -m 755 "${tmp}/piper/piper" "${piper_bin}"
  rm -rf "${tmp}"
}

download_voice() {
  local onnx="${MODELS_DIR}/pt-BR-cadu-medium.onnx"
  local json="${MODELS_DIR}/pt-BR-cadu-medium.onnx.json"
  mkdir -p "${MODELS_DIR}"
  if [[ -f "${onnx}" && -f "${json}" ]]; then
    log "Voice model already present"
    return 0
  fi
  log "Downloading Piper voice pt-BR-cadu-medium..."
  curl -fsSL "${VOICE_BASE}/pt_BR-cadu-medium.onnx" -o "${onnx}"
  curl -fsSL "${VOICE_BASE}/pt_BR-cadu-medium.onnx.json" -o "${json}"
}

setup_config() {
  local cfg="${INSTALL_DIR}/config.env"
  local example="${INSTALL_DIR}/config.env.example"
  if [[ -f "${cfg}" ]]; then
    log "Keeping existing config.env"
    return 0
  fi
  cp "${example}" "${cfg}"
  sed -i "s|@INSTALL_DIR@|${INSTALL_DIR}|g" "${cfg}"
  sed -i "s|\${HOME}|${HOME}|g" "${cfg}"
  log "Created config.env from example — edit MIC_DEVICE and WHISPER_DEVICE if needed"
}

write_wrapper() {
  local name="$1"
  local target="$2"
  local out="${BIN_DIR}/${name}"
  mkdir -p "${BIN_DIR}"
  cat > "${out}" <<EOF
#!/usr/bin/env bash
export PORCO_ASSISTANT_HOME="${INSTALL_DIR}"
exec "${target}" "\$@"
EOF
  chmod +x "${out}"
}

install_binaries() {
  log "Installing command wrappers to ${BIN_DIR}"
  write_wrapper "porco-assistant-open-agent.sh" "${INSTALL_DIR}/scripts/open-agent.sh"
  write_wrapper "porco-assistant-voice-on.sh" "${INSTALL_DIR}/scripts/voice-on.sh"
  write_wrapper "porco-assistant-voice-off.sh" "${INSTALL_DIR}/scripts/voice-off.sh"
  write_wrapper "porco-assistant-voice-stop.sh" "${INSTALL_DIR}/scripts/voice-stop.sh"
  write_wrapper "porco-assistant-agent-tts-hook.sh" "${INSTALL_DIR}/scripts/agent-tts-hook.sh"
}

install_desktop() {
  log "Installing application menu shortcuts"
  mkdir -p "${APP_DIR}"
  for f in "${INSTALL_DIR}"/desktop/*.desktop; do
    install -m 644 "${f}" "${APP_DIR}/$(basename "${f}")"
  done
  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" 2>/dev/null || true
  fi
}

install_systemd() {
  log "Installing user systemd service"
  mkdir -p "${SYSTEMD_USER}"
  sed "s|@INSTALL_DIR@|${INSTALL_DIR}|g" \
    "${INSTALL_DIR}/systemd/porco-assistant.service" \
    > "${SYSTEMD_USER}/porco-assistant.service"
  systemctl --user daemon-reload
  systemctl --user enable porco-assistant.service
  systemctl --user restart porco-assistant.service || warn "Service start failed — check logs after login"
}

setup_input_group() {
  if groups "${USER}" | grep -q '\binput\b'; then
    return 0
  fi
  warn "Adding ${USER} to group 'input' for global hotkeys (log out/in required)"
  sudo usermod -aG input "${USER}" || warn "Could not add to input group"
}

print_hook_hint() {
  cat <<'EOF'

Optional — read agent replies aloud in Cursor:
  Add a hook in Cursor settings (Hooks → afterAgentResponse):
    porco-assistant-agent-tts-hook.sh

Hotkeys (when service is running):
  Super+Z          — new agent prompt by voice
  Ctrl+Super+Z     — continue last conversation
  Ctrl+Super+A     — stop current speech

EOF
}

main() {
  arch_check
  install_packages
  setup_venv
  download_piper
  download_voice
  setup_config
  install_binaries
  install_desktop
  setup_input_group
  install_systemd
  print_hook_hint
  log "Done. Install dir: ${INSTALL_DIR}"
  log "Log file: ${INSTALL_DIR}/porco-assistant.log"
  log "Service: systemctl --user status porco-assistant.service"
}

main "$@"
