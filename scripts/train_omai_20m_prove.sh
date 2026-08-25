#!/usr/bin/env bash
# Prove OMAI-20M: own tokenizer + arch + corpus → owned checkpoint.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || true

DEVICE="${OM_TRAIN_DEVICE:-}"
if [[ -z "$DEVICE" ]]; then
  if .venv/bin/python -c "import torch; raise SystemExit(0 if torch.backends.mps.is_available() else 1)" 2>/dev/null; then
    DEVICE=mps
  elif .venv/bin/python -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    DEVICE=cuda
  else
    DEVICE=cpu
  fi
fi

STEPS="${OM_TRAIN_STEPS:-200}"
OUT="${OM_TRAIN_OUT:-artifacts/checkpoints/omai-20m-base}"

echo "=== OMAI-20M prove-the-brain ==="
echo "device=$DEVICE steps=$STEPS out=$OUT"

om-ai corpus build-v1 --root data/omai-corpus-v1 --max-docs "${OM_CORPUS_MAX_DOCS:-40}" --no-fetch || true

# Single argv array avoids "command not found" if a line-continuation backslash is missing.
om-ai train-om1 \
  --config configs/omai-20m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --data data/omai-corpus-v1/train/corpus.txt \
  --output "$OUT" \
  --steps "$STEPS" \
  --batch-size 2 \
  --checkpoint-every 50 \
  --log-every 10 \
  --device "$DEVICE" \
  --max-tokens "${OM_MAX_TOKENS:-200000}" \
  --max-docs "${OM_MAX_DOCS:-1500}"

.venv/bin/python - <<PY
import json
from pathlib import Path
out = Path("$OUT")
latest = out / "latest.pt"
status = {
    "milestone": "OMAI-20M prove-the-brain",
    "checkpoint": str(latest) if latest.is_file() else None,
    "exists": latest.is_file(),
    "bytes": latest.stat().st_size if latest.is_file() else 0,
    "config": "configs/omai-20m.json",
    "tokenizer": "artifacts/tokenizer-production-65536.json",
    "data": "data/omai-corpus-v1/train/corpus.txt",
    "device": "$DEVICE",
    "steps": int("$STEPS"),
    "owned": True,
    "note": "Prototype brain only — scale 100M→1B→7B→70B with more data/compute.",
}
Path("artifacts/OMAI_20M_STATUS.json").write_text(json.dumps(status, indent=2))
print(json.dumps(status, indent=2))
PY
