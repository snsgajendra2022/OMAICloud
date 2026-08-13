#!/usr/bin/env bash
# Pack (or list) the OM-70B Mac→server upload set.
# Includes code, configs, scripts, tokenizer, smoke corpus.
# Excludes .venv, large training checkpoints, sqlite runtime DBs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LIST_ONLY=0
OUT_DIR="${OM_AI_70B_PACK_DIR:-$ROOT/artifacts/handoff}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TAR_NAME="om70b-server-pack-${STAMP}.tar.gz"

usage() {
  cat <<'EOF'
Usage: ./scripts/pack_for_70b_server.sh [--list] [--out-dir DIR]

Creates artifacts/handoff/om70b-server-pack-<UTC>.tar.gz plus a MANIFEST.txt
of included paths. Does not pack .venv or huge checkpoint trees.

Env:
  OM_AI_70B_PACK_DIR  Override output directory (default: artifacts/handoff)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list) LIST_ONLY=1; shift ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

# Paths relative to repo root. Missing optional paths are skipped with a warning.
INCLUDE_PATHS=(
  "pyproject.toml"
  "README.md"
  ".env.example"
  "Makefile"
  "Dockerfile"
  "om_ai"
  "configs/70b.json"
  "configs/deepspeed_zero3.json"
  "configs/train_70b_gates.json"
  "configs/tiny.json"
  "scripts/train_70b.sh"
  "scripts/om70b_preflight.py"
  "scripts/pack_for_70b_server.sh"
  "docs/SERVER_70B_HANDOFF.md"
  "docs/TRAINING_70B.md"
  "docs/DISTRIBUTED_TRAINING.md"
  "docs/EXTERNAL_ASSETS_REQUIRED.md"
  "artifacts/tokenizer-production-65536.json"
  "artifacts/tokenizer-om-production.json"
  "data/production-corpus/clean/fineweb-deduped.jsonl"
)

EXISTING=()
MISSING=()
for rel in "${INCLUDE_PATHS[@]}"; do
  if [[ -e "$ROOT/$rel" ]]; then
    EXISTING+=("$rel")
  else
    MISSING+=("$rel")
  fi
done

echo "=== OM-70B server pack (repo: $ROOT) ==="
echo "Include count: ${#EXISTING[@]}"
if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "Missing (skipped):"
  printf '  - %s\n' "${MISSING[@]}"
fi
echo
echo "Paths:"
printf '  %s\n' "${EXISTING[@]}"
echo
echo "NOTE: fineweb-deduped.jsonl is ~100MB smoke data. Replace/expand on server (≥1GB for preflight)."
echo "NOTE: Excluding .venv, artifacts/checkpoints/*, *.sqlite3*, and other runtime junk."

if [[ "$LIST_ONLY" -eq 1 ]]; then
  exit 0
fi

mkdir -p "$OUT_DIR"
MANIFEST="$OUT_DIR/MANIFEST-${STAMP}.txt"
TAR_PATH="$OUT_DIR/$TAR_NAME"

{
  echo "# OM-70B server pack manifest"
  echo "# created_utc=$STAMP"
  echo "# root=$ROOT"
  echo "# archive=$TAR_PATH"
  echo "# smoke_corpus=data/production-corpus/clean/fineweb-deduped.jsonl (~100MB; expand on server)"
  echo "# tokenizer_hf=artifacts/tokenizer-production-65536.json"
  echo "# see=docs/SERVER_70B_HANDOFF.md"
  echo
  for rel in "${EXISTING[@]}"; do
    if [[ -f "$ROOT/$rel" ]]; then
      sz=$(wc -c <"$ROOT/$rel" | tr -d ' ')
      echo "FILE ${sz} ${rel}"
    else
      echo "DIR  ${rel}"
    fi
  done
} >"$MANIFEST"

# Exclude checkpoints / venv / caches even if nested under included dirs.
tar -czf "$TAR_PATH" \
  --exclude='.venv' \
  --exclude='**/__pycache__' \
  --exclude='**/*.pyc' \
  --exclude='**/.DS_Store' \
  --exclude='artifacts/checkpoints' \
  --exclude='**/*.sqlite3' \
  --exclude='**/*.sqlite3-*' \
  -C "$ROOT" \
  "${EXISTING[@]}"

# Also copy manifest into a stable name next to the tarball
cp "$MANIFEST" "$OUT_DIR/MANIFEST-latest.txt"
ln -sfn "$TAR_NAME" "$OUT_DIR/om70b-server-pack-latest.tar.gz" 2>/dev/null || true

echo
echo "Wrote: $TAR_PATH"
echo "Manifest: $MANIFEST"
ls -lah "$TAR_PATH" "$MANIFEST"
echo
echo "Upload that tarball to the GPU server, then follow docs/SERVER_70B_HANDOFF.md"
echo "First 3 server commands are listed at the bottom of that doc."
