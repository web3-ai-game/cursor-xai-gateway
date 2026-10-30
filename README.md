# Cursor xAI gateway

OpenAI-compatible LiteLLM proxy that lets Cursor call xAI with a key that never enters the IDE.

Cursor's cloud agent refuses a private-network base URL, so production puts a public reverse proxy in front of this process. This repo is the proxy only. Nginx, systemd, and the origin address are not included.

## Why the aliases look like this

- Do not name an alias `grok-4.6` or `grok-4.5`. Those collide with Cursor's built-in models, and the request never reaches this proxy.
- Cursor treats an unknown custom name as a 1M window and does not read `/v1/models`. `grok-4.6` rejects prompts past 500k. The `xai-4.6[context=400k]` alias makes Cursor compact around 400k, with room left for reasoning and tool output.

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # set XAI_API_KEY
python3 start.py
```

Listens on `127.0.0.1:4000`. `usage_logger.py` writes one JSONL row per request under `logs/`. `usage_watch.py` prints the recent rows.

```bash
python3 usage_watch.py logs/usage.jsonl 20
```
