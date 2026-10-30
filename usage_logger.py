"""LiteLLM callback: log per-request token usage for Cursor BYOK (no UI meter)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from litellm.integrations.custom_logger import CustomLogger

LOG_DIR = Path(__file__).resolve().parent / "logs"
JSONL = LOG_DIR / "usage.jsonl"
# xAI doubles price at 200k prompt tokens. Warn earlier so chats can be reset.
BUDGET = 200_000
WARN_AT = 150_000

log = logging.getLogger("grok-api.usage")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False


def _int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _attr_or_key(obj: Any, *names: str) -> Any:
    if obj is None:
        return None
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            val = getattr(obj, name)
            if val is not None:
                return val
    return None


def _extract_usage(response_obj: Any, kwargs: dict[str, Any]) -> dict[str, int]:
    usage = _attr_or_key(response_obj, "usage")
    slp = kwargs.get("standard_logging_object") or {}
    if usage is None:
        usage = slp.get("response") if isinstance(slp, dict) else None
        if isinstance(usage, dict):
            usage = usage.get("usage") or usage
        usage = usage or slp

    prompt = _int(_attr_or_key(usage, "prompt_tokens", "promptTokens"))
    completion = _int(_attr_or_key(usage, "completion_tokens", "completionTokens"))
    total = _int(_attr_or_key(usage, "total_tokens", "totalTokens"))
    details = _attr_or_key(usage, "prompt_tokens_details", "promptTokensDetails") or {}
    cached = _int(_attr_or_key(details, "cached_tokens", "cachedTokens"))
    cdetails = _attr_or_key(usage, "completion_tokens_details", "completionTokensDetails") or {}
    reasoning = _int(_attr_or_key(cdetails, "reasoning_tokens", "reasoningTokens"))

    if prompt == 0 and isinstance(slp, dict):
        prompt = _int(slp.get("prompt_tokens") or slp.get("total_tokens"))
        completion = _int(slp.get("completion_tokens"))

    if total == 0:
        total = prompt + completion
    return {
        "prompt": prompt,
        "cached": cached,
        "completion": completion,
        "reasoning": reasoning,
        "total": total,
    }


def _model_name(kwargs: dict[str, Any]) -> str:
    litellm_params = kwargs.get("litellm_params") or {}
    metadata = litellm_params.get("metadata") or {}
    return str(
        metadata.get("model_group")
        or kwargs.get("model")
        or litellm_params.get("model")
        or "?"
    )


class UsageLogger(CustomLogger):
    def __init__(self) -> None:
        super().__init__(turn_off_message_logging=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _write(self, row: dict[str, Any]) -> None:
        line = json.dumps(row, ensure_ascii=False)
        flag = "WARN" if row.get("prompt", 0) >= WARN_AT else "OK"
        print(
            f"USAGE {flag} model={row.get('model')} "
            f"prompt={row.get('prompt')}/{BUDGET} "
            f"pct={row.get('pct')} "
            f"cached={row.get('cached')} "
            f"out={row.get('completion')} "
            f"reason={row.get('reasoning')} "
            f"long={int(bool(row.get('long_context')))} "
            f"ok={int(bool(row.get('ok')))}",
            flush=True,
        )
        try:
            with JSONL.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            log.warning("usage jsonl write failed: %s", exc)

    def _row(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        ok: bool,
        error: str | None = None,
    ) -> dict[str, Any]:
        usage = _extract_usage(response_obj, kwargs)
        prompt = usage["prompt"]
        row = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ok": ok,
            "model": _model_name(kwargs),
            "prompt": prompt,
            "cached": usage["cached"],
            "completion": usage["completion"],
            "reasoning": usage["reasoning"],
            "total": usage["total"],
            "pct": round(100.0 * prompt / BUDGET, 1) if BUDGET else 0,
            "long_context": prompt >= BUDGET,
            "warn": prompt >= WARN_AT,
        }
        if error:
            row["error"] = error[:240]
        return row

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        self._write(self._row(kwargs, response_obj, True))

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        err = ""
        if isinstance(kwargs, dict):
            err = str(kwargs.get("exception") or "")
        self._write(self._row(kwargs or {}, response_obj, False, err or "error"))

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        self.log_success_event(kwargs, response_obj, start_time, end_time)

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        self.log_failure_event(kwargs, response_obj, start_time, end_time)


proxy_handler_instance = UsageLogger()
