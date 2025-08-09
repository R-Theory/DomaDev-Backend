#!/usr/bin/env bash
set -euo pipefail

# cd to repo root (script may be called from anywhere)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="${SCRIPT_DIR%/scripts}"
cd "$ROOT_DIR"

export PYTHONUNBUFFERED=1
export API_PORT=${API_PORT:-${PORT:-5050}}

# 1) Ensure venv
if [[ ! -d .venv ]]; then
  echo "[setup] creating venv (.venv)"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# 2) Install deps (idempotent)
pip install -q -r requirements.txt

# 3) Ensure .env exists with safe defaults (non-destructive)
if [[ ! -f .env ]]; then
  echo "[setup] writing minimal .env"
  cat > .env <<EOF
API_PORT=${API_PORT}
LOG_LEVEL=INFO
ALLOW_ORIGINS=["*"]
# Configure your route to local vLLM (TinyLlama on :8000 by default)
MODEL_ROUTE_tiny=http://localhost:8000/v1
DEFAULT_MODEL_KEY=tiny
DEFAULT_MODEL_NAME=TinyLlama/TinyLlama-1.1B-Chat-v1.0
# Set API_KEY to protect endpoints (except /health). Example:
# API_KEY=$(python -c 'import secrets;print(secrets.token_hex(32))')
EOF
fi

# 4) Start server (reload enabled)
chmod +x scripts/*.sh || true
exec uvicorn app.main:app --host 0.0.0.0 --port "$API_PORT" --reload
