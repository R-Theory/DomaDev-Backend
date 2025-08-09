#!/usr/bin/env bash
set -euo pipefail

# Usage examples:
#   ./scripts/start_vllm.sh --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --port 8000 --served-model-name TinyLlama/TinyLlama-1.1B-Chat-v1.0
#   ./scripts/start_vllm.sh --model microsoft/Phi-4 --port 8001 --served-model-name microsoft/Phi-4

MODEL=""
PORT=8000
SERVE_NAME=""
DOWNLOAD_DIR=""
HF_HOME_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="$2"; shift 2 ;;
    --port)
      PORT="$2"; shift 2 ;;
    --served-model-name)
      SERVE_NAME="$2"; shift 2 ;;
    --download-dir)
      DOWNLOAD_DIR="$2"; shift 2 ;;
    --hf-home)
      HF_HOME_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$MODEL" ]]; then
  echo "--model is required" >&2
  exit 1
fi

if [[ -n "$HF_HOME_DIR" ]]; then
  export HF_HOME="$HF_HOME_DIR"
fi

EXTRA_ARGS=()
if [[ -n "$DOWNLOAD_DIR" ]]; then
  EXTRA_ARGS+=("--download-dir" "$DOWNLOAD_DIR")
fi
if [[ -n "$SERVE_NAME" ]]; then
  EXTRA_ARGS+=("--served-model-name" "$SERVE_NAME")
fi

exec python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --host 0.0.0.0 \
  --port "$PORT" \
  "${EXTRA_ARGS[@]}"
