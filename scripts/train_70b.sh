#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${OM_AI_70B_DATA:?Set OM_AI_70B_DATA=/path/to/licensed/corpus}"
: "${OM_AI_70B_TOKENIZER:?Set OM_AI_70B_TOKENIZER=/path/to/production/tokenizer.json}"

OM_AI_70B_CONFIG="${OM_AI_70B_CONFIG:-configs/70b.json}"
OM_AI_70B_OUTPUT="${OM_AI_70B_OUTPUT:-artifacts/checkpoints/om-70b}"
OM_AI_70B_DEEPSPEED="${OM_AI_70B_DEEPSPEED:-configs/deepspeed_zero3.json}"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
elif [[ -x "$ROOT/.venv/bin/python3" ]]; then
  PYTHON="$ROOT/.venv/bin/python3"
else
  PYTHON="$(command -v python3)"
fi

"$PYTHON" "$ROOT/scripts/om70b_preflight.py" \
  --config "$OM_AI_70B_CONFIG" \
  --data "$OM_AI_70B_DATA" \
  --tokenizer "$OM_AI_70B_TOKENIZER"

if ! command -v deepspeed >/dev/null 2>&1; then
  echo "ERROR: deepspeed not found on PATH. Install on a CUDA cluster: pip install -e '.[deepSpeed]'" >&2
  echo "Refusing to start OM-70B training without DeepSpeed+CUDA." >&2
  exit 2
fi

exec deepspeed "$ROOT/om_ai/training/deepspeed_train.py" \
  --config "$OM_AI_70B_CONFIG" \
  --data "$OM_AI_70B_DATA" \
  --tokenizer "$OM_AI_70B_TOKENIZER" \
  --deepspeed "$OM_AI_70B_DEEPSPEED" \
  --output "$OM_AI_70B_OUTPUT"
