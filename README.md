# cursor-xai-gateway

讓 Cursor 呼叫 xAI，而金鑰不進 IDE。這是一個 OpenAI 相容的 LiteLLM 代理。

An OpenAI-compatible LiteLLM proxy. Cursor calls xAI. The key never enters the IDE.

Cursor 的雲端代理拒絕私網位址。正式環境在這個行程前面放一台公開的反向代理。這個庫只有代理本身。nginx、systemd 和原點位址沒有附上。

Cursor's cloud agent refuses a private-network base URL. Production puts a public reverse proxy in front of this process. This repo is the proxy only. Nginx, systemd, and the origin address are not included.

## 別名為什麼長這樣

這兩條是正式環境撞出來的，不是圖上畫的。

These two rules came out of production, not from a diagram.

- 別名不要用 `grok-4.6` 或 `grok-4.5`。那是 Cursor 內建名稱。請求會被 Cursor 自己吃掉，到不了這個代理。Do not name an alias `grok-4.6` or `grok-4.5`. Those are Cursor built-ins. Cursor keeps the request, and it never reaches this proxy.
- Cursor 把目錄裡沒有的自訂名稱當成 100 萬 token 視窗，而且不讀 `/v1/models`。`grok-4.6` 的上游上限是 50 萬。等到上游拒絕才壓縮，已經太晚。`xai-4.6[context=400k]` 讓 Cursor 在大約 40 萬就壓縮，留下推理和工具輸出的空間。Cursor treats an unknown custom name as a 1M window and does not read `/v1/models`. The upstream cap on `grok-4.6` is 500k. Waiting for the upstream to reject the prompt is too late to compress. The `xai-4.6[context=400k]` alias makes Cursor compact around 400k.

## 本地執行

需要 Python 3.11 以上。

Needs Python 3.11 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填 XAI_API_KEY。Edit .env and set XAI_API_KEY.
.venv/bin/python start.py
```

聽在 `127.0.0.1:4000`。`usage_logger.py` 每個請求寫一列 JSONL 到 `logs/`。`usage_watch.py` 印出最近的列。

Listens on `127.0.0.1:4000`. `usage_logger.py` writes one JSONL row per request under `logs/`. `usage_watch.py` prints the recent rows.

```bash
.venv/bin/python usage_watch.py logs/usage.jsonl 20
```

| 變數 | 用途 |
|---|---|
| `XAI_API_KEY` | 上游金鑰。只放在這台機器。Upstream key. This machine only. |
| `LITELLM_MASTER_KEY` | 代理自己的門禁。`.env.example` 留空。沒填時，`start.py` 才在本機行程補一個只給 localhost 的值。The proxy's own gate. `.env.example` is empty. If unset, `start.py` fills a localhost-only value in the process. |

## 檔案

| 檔案 | 職責 |
|---|---|
| `config.yaml` | 別名、視窗、上游。Aliases, windows, upstream. |
| `start.py` | 讀 `.env`，在 `127.0.0.1:4000` 啟動 LiteLLM。Loads `.env` and starts LiteLLM. |
| `usage_logger.py` | 每個請求一列。One row per request. |
| `usage_watch.py` | 看最近的用量。Prints recent usage. |

## 授權

[MIT](LICENSE)。這個庫沒有原點位址，也沒有金鑰。
