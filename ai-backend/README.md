# AI Backend Gateway over vLLM

> A production-ready FastAPI gateway that proxies multiple local vLLM OpenAI-compatible servers and exposes a clean, consistent API for chat (including SSE streaming), embeddings, and model management.

## Why this exists
- **Fast local iteration**: Run vLLM locally and consume a stable API from your frontend.
- **Multi-instance routing**: Route by `modelKey` or infer by `model` across multiple vLLM instances.
- **Ops ready**: API key auth, rate limiting, structured logs, Prometheus metrics, and docs.

## Prerequisites
- WSL2 (Ubuntu 24.04)
- Python 3.12
- vLLM running on Ubuntu/WSL2 (OpenAI-compatible server). Example script: `./scripts/start_vllm.sh`.
- Typical model: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`. The gateway runs on Linux or Windows and proxies vLLM.
- Optional: HuggingFace token for gated models; set `HF_HOME` and `--download-dir` as needed.

## Quick start
```bash
# 1) Create venv and install deps
cd ai-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2) Configure
cp .env.example .env
# edit .env to set MODEL_ROUTE_* and DEFAULT_MODEL_KEY/NAME

# 3) Run API
./scripts/dev.sh

# 4) Health check
curl -s localhost:5050/health | jq
```

Windows note: You can launch the gateway with `START-HERE.bat` or `start-backend.ps1`. Ensure your vLLM instance is reachable (e.g., WSL2 on `http://localhost:8000`).

## Configuration (env)
- `API_PORT` (default 5050) – server port. Fallback to `PORT`.
- `LOG_LEVEL` – INFO, DEBUG, etc.
- `ALLOW_ORIGINS` – CORS allowlist (CSV or `*`).
- `API_KEY` – if set, required via `X-API-Key` for all endpoints except `/health` (and `/metrics` if `METRICS_PUBLIC=true`).
- `AUTH_REQUIRED` – set `false` to disable auth even if `API_KEY` is set.
- `METRICS_PUBLIC` – set `true` to expose `/metrics` without auth.
- `MODEL_ROUTE_<KEY>=http://host:port/v1` – map a `modelKey` to a vLLM base URL.
- `DEFAULT_MODEL_KEY` – default route key when not specified.
- `DEFAULT_MODEL_NAME` – default model ID when not provided (e.g., `TinyLlama/TinyLlama-1.1B-Chat-v1.0`).
- `ALLOWED_MODELS` – CSV allowlist (filters `/models` and validates requests).
- `VLLM_BASE_URL` – legacy single-route fallback if `MODEL_ROUTE_*` not provided.
- `RATE_LIMIT_PER_MIN` – per-IP capacity.
- `USE_REDIS`/`REDIS_URL` – enable Redis-backed rate limiting.
- `CONNECT_TIMEOUT_SECONDS`, `READ_TIMEOUT_SECONDS`, `WRITE_TIMEOUT_SECONDS`, `TOTAL_TIMEOUT_SECONDS` – upstream timeouts.
- `PROMETHEUS_ENABLE` – enable `/metrics` (default: true).
- `SSE_HEARTBEAT_SECONDS` – heartbeat interval for `/api/chat/stream` (default 15).

## Multi-model routing (multi-instance)
- Provide routes: `MODEL_ROUTE_tiny=http://localhost:8000/v1` (add more as needed).
- Set `DEFAULT_MODEL_KEY=tiny`.
- Requests can include `modelKey` to select the instance explicitly.
- If no `modelKey`, the gateway attempts to infer the route by querying `/v1/models` (cached 10s). If exactly one instance serves the `model`, it routes there; otherwise 409.

## API
All routes are under `/api` (except `/health` and `/metrics`).

### GET /health
Response (derives `vllm` by probing the default/first route’s `/models`):
```json
{ "ok": true, "vllm": "ok|unavailable|unconfigured|unknown" }
```

### GET /api/models
Aggregates models from all routes, de-dupes by id, and includes sources and latency:
```json
{
  "object": "list",
  "data": [
    { "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "object": "model", "sources": [{"source": "tiny", "latency_ms": 42}] }
  ]
}
```
Respects `ALLOWED_MODELS`.

### POST /api/chat
Body:
```json
{
  "message": "Hello",
  "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "modelKey": "tiny",
  "system": "You are helpful.",
  "temperature": 0.2,
  "max_tokens": 256
}
```
Response is the upstream OpenAI-compatible JSON.

Error codes:
- 403 when blocked by allowlist
- 409 when routing/availability mismatch
- 504 upstream timeout; 502 connection errors

### POST /api/chat/stream
SSE stream (text/event-stream) that forwards upstream chunks and sends heartbeats every ~15s.
Curl example:
```bash
curl -N -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","model":"TinyLlama/TinyLlama-1.1B-Chat-v1.0","modelKey":"tiny"}' \
  http://localhost:5050/api/chat/stream
```
Heartbeats are sent as SSE comments like `: keepalive` roughly every `SSE_HEARTBEAT_SECONDS` seconds.

### POST /api/embeddings
Body:
```json
{ "input": "some text", "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "modelKey": "tiny" }
```
Response is the upstream OpenAI-compatible JSON.

## Observability
- `/metrics` exposes Prometheus metrics (protected unless `METRICS_PUBLIC=true`).
- vLLM also exposes `/metrics` on its own ports; scrape both for a full picture.

## Auth & rate limiting
- Set `API_KEY` to require `X-API-Key` for all endpoints except `/health` (and `/metrics` with `METRICS_PUBLIC=true`).
- In-memory per-IP token bucket (default 60 req/min). Optional Redis backend with `USE_REDIS=true` and `REDIS_URL`.

## Testing
```bash
pytest -q
```
Tests use FastAPI test client and do not require a running vLLM.

## Production notes
- Use `systemd` units for both the API and vLLM processes.
- Tighten CORS (`ALLOW_ORIGINS`), configure logging aggregation, ensure graceful shutdown.
- Store HuggingFace cache on a persistent drive (`HF_HOME`, `--download-dir`, e.g., `/mnt/d/hf-cache`).
- Back up your WSL distro periodically.

## Troubleshooting
- CUDA/driver issues under WSL: ensure NVIDIA drivers and CUDA toolkit match.
- Port conflicts: adjust `API_PORT` or vLLM ports.
- Model routing 409: verify the requested `model` is served by the selected `modelKey` or available for inference.
