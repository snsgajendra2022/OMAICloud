#!/usr/bin/env bash
# Honest OM-1.0 native train on this Mac (no Ollama / no OpenAI).
# This is NOT ChatGPT: configs/om-1.0-local.json is ~20M params, max_seq_len=128.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Prefer 1GB FineWeb if present; 100MB file is too small to keep looping forever.
DATA="data/production-corpus/clean/fineweb-1gb.jsonl"
if [[ ! -f "$DATA" ]]; then
  DATA="data/production-corpus/raw/fineweb-100mb.txt"
fi
exec om-ai train-om1 \
  --config configs/om-1.0-local.json \
  --data "$DATA" \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --steps 50000 \
  --batch-size 4 \
  --max-tokens 2000000 \
  --max-docs 20000 \
  --checkpoint-every 1000 \
  --log-every 50 \
  --device mps \
  --precision auto \
  --resume artifacts/checkpoints/om-1.0-base/latest.pt \
  --output artifacts/checkpoints/om-1.0-base
