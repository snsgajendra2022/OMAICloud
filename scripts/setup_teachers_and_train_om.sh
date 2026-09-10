#!/usr/bin/env bash
# Install Ollama teachers + pull models + run OM learn/SFT.
# Run this in your own Terminal (needs disk space + network).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Disk ==="
df -h . | tail -1
echo
echo "NOTE: qwen3:14b + deepseek-r1:14b + mistral + llama3.3 need tens of GB."
echo "Your free space may only allow smaller pulls first (mistral, then one 14b)."
echo

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama (macOS)..."
  if [[ -d /Applications/Ollama.app ]]; then
    open -a Ollama || true
  elif command -v brew >/dev/null 2>&1; then
    brew install --cask ollama
    open -a Ollama || true
  else
    echo "Install from https://ollama.com/download then re-run this script."
    exit 1
  fi
  sleep 3
fi

# Ensure daemon is up
ollama serve >/tmp/ollama-serve.log 2>&1 &
sleep 2 || true

export OM_TEACHER_MODELS="qwen3:14b,deepseek-r1:14b,mistral:latest,llama3.3"
export OM_OLLAMA_BASE_URL="http://127.0.0.1:11434"

MODELS=(
  "mistral:latest"
  "qwen3:14b"
  "deepseek-r1:14b"
  "llama3.3"
)

for m in "${MODELS[@]}"; do
  echo "=== Pulling $m ==="
  if ! ollama pull "$m"; then
    echo "WARN: failed to pull $m (disk/network). Continuing."
  fi
done

echo "=== Ollama models ==="
ollama list || true

echo "=== Teacher distill / learn harvest ==="
.venv/bin/om-ai distill models || true
.venv/bin/om-ai learn start --topic "software engineering" --count 20 --max-items 10 || true
.venv/bin/om-ai learn start --topic "React architecture" --count 10 --max-items 10 || true
.venv/bin/om-ai distill topic --topic "Kubernetes architecture" --count 5 --parallelism 2 || true

echo "=== Merge all training JSONL ==="
.venv/bin/python scripts/merge_all_sft.py

echo "=== Train OM (SFT) on merged corpus ==="
.venv/bin/om-ai sft \
  --config configs/om-1.0-local.json \
  --data data/training/om_all_sft_merged.jsonl \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt \
  --output artifacts/checkpoints/om-1.0-distill-sft \
  --steps 500 \
  --batch-size 1 \
  --grad-accum 4 \
  --lr 1e-5 \
  --checkpoint-every 100 \
  --device mps

echo "DONE. New checkpoint: artifacts/checkpoints/om-1.0-distill-sft/"
