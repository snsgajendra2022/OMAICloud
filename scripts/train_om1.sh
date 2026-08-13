#!/usr/bin/env bash
# OM-1.0 local smoke train — truthful, not 70B.
# Uses streaming corpus load; writes artifacts/checkpoints/om-1.0-smoke/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV_PY="${ROOT}/.venv/bin/om-ai"
if [[ ! -x "$VENV_PY" ]]; then
  VENV_PY="om-ai"
fi

CONFIG="${OM_MODEL_CONFIG:-configs/om-1.0-local.json}"
TOKENIZER="${OM_MODEL_TOKENIZER:-artifacts/tokenizer-fixed-v3.json}"
DATA="${OM_MODEL_DATA:-}"
if [[ -z "$DATA" ]]; then
  if [[ -f data/production-corpus/shards/shard-00000.jsonl ]]; then
    DATA="data/production-corpus/shards/shard-00000.jsonl"
  elif [[ -f data/production-corpus/clean/fineweb-deduped.jsonl ]]; then
    DATA="data/production-corpus/clean/fineweb-deduped.jsonl"
  else
    echo "No corpus found; set OM_MODEL_DATA=/path/to.jsonl" >&2
    exit 1
  fi
fi
OUTPUT="${OM_MODEL_OUTPUT:-artifacts/checkpoints/om-1.0-smoke}"
STEPS="${OM_MODEL_STEPS:-20}"
DEVICE="${OM_MODEL_DEVICE:-}"

ARGS=(
  train-om1
  --config "$CONFIG"
  --data "$DATA"
  --tokenizer "$TOKENIZER"
  --output "$OUTPUT"
  --steps "$STEPS"
  --batch-size "${OM_MODEL_BATCH_SIZE:-4}"
  --max-tokens "${OM_MODEL_MAX_TOKENS:-250000}"
  --max-docs "${OM_MODEL_MAX_DOCS:-2000}"
  --log-every 1
  --checkpoint-every 10
)
if [[ -n "$DEVICE" ]]; then
  ARGS+=(--device "$DEVICE")
fi

echo "Running: $VENV_PY ${ARGS[*]}"
exec "$VENV_PY" "${ARGS[@]}"
