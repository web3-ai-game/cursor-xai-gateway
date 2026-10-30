#!/usr/bin/env python3
"""Show recent Cursor→xAI token usage from the LiteLLM jsonl log."""

from __future__ import annotations

import json
import sys
from pathlib import Path

JSONL = Path(__file__).resolve().parent / "logs" / "usage.jsonl"
BUDGET = 200_000


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else JSONL
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    if not path.is_file():
        sys.exit(f"no usage log yet: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for raw in lines[-n:]:
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    print(f"{'ts':<22} {'ok':<3} {'model':<12} {'prompt':>8} {'pct':>6} {'cached':>8} {'out':>6} {'reason':>7}  flag")
    for row in rows:
        prompt = int(row.get("prompt") or 0)
        pct = row.get("pct")
        if pct is None:
            pct = round(100.0 * prompt / BUDGET, 1)
        flag = "LONG>$" if row.get("long_context") else ("WARN" if row.get("warn") else "")
        print(
            f"{str(row.get('ts', '')):<22} "
            f"{'Y' if row.get('ok') else 'N':<3} "
            f"{str(row.get('model', '')):<12} "
            f"{prompt:>8} {pct:>5}% "
            f"{int(row.get('cached') or 0):>8} "
            f"{int(row.get('completion') or 0):>6} "
            f"{int(row.get('reasoning') or 0):>7}  {flag}"
        )
    print()
    print("pct = prompt / 200k (xAI long-context price cliff). New Agent chat if WARN or LONG.")
    print("journal: journalctl -u grok-api -g '^USAGE' -n 30 --no-pager")
    print("413 body: grep 'too large body' /var/log/nginx/error.log | tail")


if __name__ == "__main__":
    main()
