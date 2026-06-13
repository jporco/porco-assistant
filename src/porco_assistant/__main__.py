"""python -m porco_assistant"""

from __future__ import annotations

import sys
from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from porco_assistant.daemon import Daemon
from porco_assistant.env import carregar


def main() -> int:
    carregar()
    return Daemon().run()


if __name__ == "__main__":
    raise SystemExit(main())
