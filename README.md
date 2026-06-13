# Porco Assistant

Voice-driven control for **Cursor IDE** on Linux (X11). Push-to-talk sends prompts to Cursor Agents without keeping focus on the editor; optional text-to-speech reads agent replies.

## Features

- **Super+Z** — speak a new prompt to the Cursor agent  
- **Ctrl+Super+Z** — continue the last agent conversation  
- **Ctrl+Super+A** — stop current speech  
- Optional TTS for agent responses (menu shortcuts or Cursor hook)  
- Runs as a user systemd service after graphical login  

## Requirements

| Component | Notes |
|-----------|--------|
| **OS** | Arch Linux or derivative (`pacman`) |
| **Session** | X11 (Plasma, Xfce, GNOME on Xorg, etc.) |
| **Cursor IDE** | Installed and logged in; Agents / Chat available |
| **Cursor CLI** | `agent` command on `PATH` (from Cursor) |
| **Audio** | Microphone + speakers/headphones (`aplay`, PipeWire/PulseAudio) |
| **GPU (optional)** | NVIDIA + CUDA for faster speech recognition (`WHISPER_DEVICE=cuda` in `config.env`) |

System packages installed by the installer: `python`, `ffmpeg`, `alsa-utils`, `xdotool`, `xclip`, `libnotify`, and Python deps via `pip` (`faster-whisper`, `sounddevice`, `evdev`, …).

Piper TTS binary and the **pt-BR-cadu-medium** voice are downloaded automatically on first install.

## Install

```bash
git clone https://github.com/jporco/porco-assistant.git
cd porco-assistant
chmod +x install.sh
./install.sh
```

The script creates a virtualenv, downloads Piper + voice model, installs menu shortcuts, wrappers in `~/.local/bin`, and enables `porco-assistant.service` for your user.

After install, edit `config.env` if needed:

- `MIC_DEVICE` — substring of your mic name or device index  
- `WHISPER_DEVICE` — `cpu` (default) or `cuda`  

If hotkeys do not work, log out and back in after being added to the `input` group.

### Optional: TTS hook in Cursor

In Cursor → Settings → Hooks → **afterAgentResponse**, point to:

```text
porco-assistant-agent-tts-hook.sh
```

Enable reading via the application menu: **Porco Assistant — Enable agent voice**.

## Uninstall

```bash
./uninstall.sh
```

Removes the systemd unit, menu entries, and wrappers. Project files stay on disk until you delete the folder.

## Service

```bash
systemctl --user status porco-assistant.service
systemctl --user restart porco-assistant.service
```

Logs: `porco-assistant.log` in the install directory.

---

## Porco Assistant (PT)

Assistente de voz para o **Cursor** no Linux. Fale o comando, o agente recebe o texto; dá para ouvir as respostas em voz alta.

Instalação: clone o repositório e execute `./install.sh`. Atalhos aparecem no menu do sistema. Ajuste microfone e GPU em `config.env` se precisar.

Atalhos: **Super+Z** (novo), **Ctrl+Super+Z** (continuar), **Ctrl+Super+A** (parar fala).

Licença: MIT
