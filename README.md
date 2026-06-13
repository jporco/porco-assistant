# Porco Assistant

Voice control for **Cursor IDE** on Linux (X11). Push-to-talk sends prompts to agents without stealing focus; optional TTS reads replies aloud.

## Features

- **Super+Z** — new agent prompt
- **Ctrl+Super+Z** — continue last conversation
- **Ctrl+Super+A** — stop speech immediately
- App menu — enable / disable agent TTS
- User systemd service

## Requirements

- Arch Linux or derivative (`pacman`)
- X11 session; Cursor IDE + `agent` CLI on `PATH`
- Microphone and speakers (`aplay`, PipeWire/Pulse)
- Optional NVIDIA CUDA for faster speech recognition

## Install

```bash
git clone https://github.com/jporco/porco-assistant.git
cd porco-assistant
chmod +x install.sh
./install.sh
```

Edit `config.env` for mic name and `WHISPER_DEVICE` (`cpu` or `cuda`). Re-login if hotkeys fail (installer adds you to the `input` group).

Optional TTS: Cursor → Hooks → **afterAgentResponse** → `porco-assistant-agent-tts-hook.sh`, then enable voice in the app menu.

## Uninstall

```bash
./uninstall.sh
```

## Service

```bash
systemctl --user restart porco-assistant.service
```

Log: `porco-assistant.log` in the install directory.

---

## Porco Assistant (PT)

Controle por voz do **Cursor** no Linux (X11). Push-to-talk envia prompts aos agentes sem roubar foco; TTS opcional lê as respostas em voz alta.

### Recursos

- **Super+Z** — novo prompt ao agente
- **Ctrl+Super+Z** — continuar última conversa
- **Ctrl+Super+A** — parar fala na hora
- Menu do sistema — ativar / desativar voz do agente
- Serviço systemd de usuário

### Requisitos

- Arch Linux ou derivado (`pacman`)
- Sessão X11; Cursor IDE + CLI `agent` no `PATH`
- Microfone e saída de áudio (`aplay`, PipeWire/Pulse)
- CUDA NVIDIA opcional para reconhecimento de voz mais rápido

### Instalação

```bash
git clone https://github.com/jporco/porco-assistant.git
cd porco-assistant
chmod +x install.sh
./install.sh
```

Edite `config.env` para o microfone e `WHISPER_DEVICE` (`cpu` ou `cuda`). Re-login se os atalhos falharem (instalador adiciona ao grupo `input`).

TTS opcional: Cursor → Hooks → **afterAgentResponse** → `porco-assistant-agent-tts-hook.sh`; depois ative a voz no menu do sistema.

### Desinstalar

```bash
./uninstall.sh
```

### Serviço

```bash
systemctl --user restart porco-assistant.service
```

Log: `porco-assistant.log` na pasta de instalação.
