#!/bin/bash

echo "Starting vLLM server manually..."

# Change to project directory
cd "/Projects/Doma Backend/Program/ai-backend" || {
    echo "ERROR: Cannot cd to project directory"
    exit 1
}

# Activate virtual environment
source .vllm-venv/bin/activate

# Check if vLLM is installed
if ! python -c "import vllm" 2>/dev/null; then
    echo "vLLM not installed. Installing..."
    python -m pip install --upgrade pip
    python -m pip install vllm
fi

echo "Starting vLLM server on port 8000..."
python -m vllm.entrypoints.openai.api_server \
    --model "TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
