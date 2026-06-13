"""Autenticação agent CLI via sessão do Cursor."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import subprocess
from pathlib import Path

logger = logging.getLogger("jarvis.auth")

_AUTH = Path.home() / ".config/cursor/auth.json"
_IDE_DB = Path.home() / ".config/Cursor/User/globalStorage/state.vscdb"


def _logado() -> bool:
    env = {k: v for k, v in os.environ.items() if k != "CURSOR_API_KEY"}
    try:
        r = subprocess.run(
            ["agent", "status"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        return "Logged in" in (r.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return False


def _tokens_ide() -> tuple[str, str] | None:
    if not _IDE_DB.is_file():
        return None
    try:
        conn = sqlite3.connect(f"file:{_IDE_DB}?mode=ro", uri=True, timeout=5.0)
        a = conn.execute(
            "SELECT value FROM ItemTable WHERE key='cursorAuth/accessToken'"
        ).fetchone()
        r = conn.execute(
            "SELECT value FROM ItemTable WHERE key='cursorAuth/refreshToken'"
        ).fetchone()
        conn.close()
        if a and r:
            return a[0], r[0]
    except Exception as exc:
        logger.warning("tokens IDE: %s", exc)
    return None


def garantir() -> bool:
    if _logado():
        return True
    tok = _tokens_ide()
    if tok:
        _AUTH.parent.mkdir(parents=True, exist_ok=True)
        _AUTH.write_text(
            json.dumps({"accessToken": tok[0], "refreshToken": tok[1]}),
            encoding="utf-8",
        )
        _AUTH.chmod(0o600)
        if _logado():
            return True
    try:
        subprocess.run(
            ["agent", "login"],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "NO_OPEN_BROWSER": "1", "DISPLAY": ":0"},
        )
    except (OSError, subprocess.SubprocessError):
        pass
    return _logado()
