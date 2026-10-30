#!/usr/bin/env python3
"""Load .env and start LiteLLM proxy on 127.0.0.1:4000."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_env(path: Path) -> None:
    if not path.is_file():
        sys.exit(f"Missing {path}. Copy .env.example to .env and set XAI_API_KEY.")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip().strip("'").strip('"')


def main() -> None:
    load_env(ROOT / ".env")
    if not os.environ.get("XAI_API_KEY"):
        sys.exit("XAI_API_KEY is empty in .env")
    if not os.environ.get("LITELLM_MASTER_KEY"):
        os.environ["LITELLM_MASTER_KEY"] = "sk-local"

    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    sys.argv = [
        "litellm",
        "--config",
        str(ROOT / "config.yaml"),
        "--host",
        "127.0.0.1",
        "--port",
        "4000",
    ]
    from litellm import run_server

    run_server()


if __name__ == "__main__":
    main()
