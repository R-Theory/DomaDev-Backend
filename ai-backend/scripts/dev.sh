#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED=1
export UVICORN_WORKERS=${UVICORN_WORKERS:-1}
export API_PORT=${API_PORT:-${PORT:-5050}}

exec uvicorn app.main:app --host 0.0.0.0 --port "$API_PORT" --reload
