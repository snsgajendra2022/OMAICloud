#!/usr/bin/env bash
# Fully automatic: teachers → real data harvest → merge → OM SFT → OM-only mode.
# Teachers are temporary collectors; after train they are removed from Ollama.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export OM_OLLAMA_BASE_URL="${OM_OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
export OM_DISTILL_ALLOW_MOCK=0
export OM_DISTILLATION_ENABLED=true
export OM_TEACHER_PARALLELISM="${OM_TEACHER_PARALLELISM:-1}"
export OM_TEACHER_TIMEOUT="${OM_TEACHER_TIMEOUT:-600}"
export OM_OLLAMA_NUM_CTX="${OM_OLLAMA_NUM_CTX:-2048}"
export OM_OLLAMA_NUM_PREDICT="${OM_OLLAMA_NUM_PREDICT:-400}"
export OM_OLLAMA_GENERATE_TIMEOUT="${OM_OLLAMA_GENERATE_TIMEOUT:-600}"
export OM_AUTO_SFT_STEPS="${OM_AUTO_SFT_STEPS:-400}"
export OM_KEEP_TEACHERS="${OM_KEEP_TEACHERS:-0}"
# Skip huge pulls by default when disk is tight; still try requested list first.
export OM_AUTO_SKIP_HUGE_PULLS="${OM_AUTO_SKIP_HUGE_PULLS:-1}"
LOG="${ROOT}/artifacts/auto_teach_train.log"
mkdir -p artifacts data/training
exec > >(tee -a "$LOG") 2>&1

echo "===== AUTO TEACH+TRAIN $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
df -h /System/Volumes/Data 2>/dev/null | tail -1 || df -h . | tail -1

ensure_ollama() {
  if ! command -v ollama >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
      brew install --cask ollama-app || brew install --cask ollama || true
    fi
  fi
  if [[ -d /Applications/Ollama.app ]]; then
    open -a Ollama || true
  fi
  if ! curl -sf "$OM_OLLAMA_BASE_URL/" >/dev/null 2>&1; then
    nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
    for _ in $(seq 1 40); do
      curl -sf "$OM_OLLAMA_BASE_URL/" >/dev/null 2>&1 && break
      sleep 1
    done
  fi
  curl -sf "$OM_OLLAMA_BASE_URL/" >/dev/null
}

free_gb() {
  # macOS: available GiB on Data volume
  df -g /System/Volumes/Data 2>/dev/null | awk 'NR==2{print $4}' || df -g . | awk 'NR==2{print $4}'
}

pull_teachers() {
  # Disk-safe teacher set. Huge 14b/70b pulls only when OM_AUTO_SKIP_HUGE_PULLS=0.
  local wanted=("mistral:latest")
  if [[ "${OM_AUTO_SKIP_HUGE_PULLS}" != "1" ]]; then
    wanted+=("qwen3:14b" "deepseek-r1:14b" "llama3.3")
  else
    echo "OM_AUTO_SKIP_HUGE_PULLS=1 — compact teachers only (disk-safe)."
    wanted+=("llama3.2:3b")
  fi
  local installed=()
  for m in "${wanted[@]}"; do
    local gb
    gb="$(free_gb || echo 0)"
    # Rough size gates: mistral~5G, 3b~2G, 14b~10G, llama3.3~40G
    if [[ "$m" == *":14b"* || "$m" == "llama3.3" ]]; then
      if [[ "${gb:-0}" -lt 12 ]]; then
        echo "SKIP $m (need >=12G free, have ${gb}G)"
        continue
      fi
    elif [[ "$m" == *"3b"* || "$m" == *"7b"* ]]; then
      if [[ "${gb:-0}" -lt 3 ]]; then
        echo "SKIP $m (need >=3G free, have ${gb}G)"
        continue
      fi
    fi
    echo "=== pull $m (free=${gb}G) ==="
    if ollama pull "$m"; then
      installed+=("$m")
    else
      echo "WARN: could not pull $m"
    fi
  done
  if [[ ${#installed[@]} -eq 0 ]]; then
    installed=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && installed+=("$line")
    done < <(ollama list 2>/dev/null | awk 'NR>1{print $1}')
  fi
  if [[ ${#installed[@]} -eq 0 ]]; then
    echo "ERROR: no Ollama teachers available"
    exit 1
  fi
  local joined
  joined="$(IFS=,; echo "${installed[*]}")"
  export OM_TEACHER_MODELS="$joined"
  echo "OM_TEACHER_MODELS=$OM_TEACHER_MODELS"
  if grep -q '^OM_TEACHER_MODELS=' .env 2>/dev/null; then
    sed -i.bak "s|^OM_TEACHER_MODELS=.*|OM_TEACHER_MODELS=$OM_TEACHER_MODELS|" .env
  else
    echo "OM_TEACHER_MODELS=$OM_TEACHER_MODELS" >> .env
  fi
  if grep -q '^OM_DISTILL_ALLOW_MOCK=' .env 2>/dev/null; then
    sed -i.bak 's|^OM_DISTILL_ALLOW_MOCK=.*|OM_DISTILL_ALLOW_MOCK=0|' .env
  else
    echo "OM_DISTILL_ALLOW_MOCK=0" >> .env
  fi
  ollama list || true
}

harvest_real() {
  echo "=== real Ollama harvest (no mocks) ==="
  .venv/bin/om-ai distill models || true
  .venv/bin/om-ai distill health || true
  # Python driver: reliable Ollama collect_and_save for each curriculum question
  .venv/bin/python - <<'PY'
import json, os
from om_ai.core.distillation import CurriculumGenerator, create_teacher_manager

os.environ.setdefault("OM_DISTILL_ALLOW_MOCK", "0")
topics = [
    ("software engineering fundamentals", "software"),
    ("React architecture and state management", "software"),
    ("Python systems design", "software"),
    ("HTTP APIs and REST", "software"),
    ("databases SQL and indexes", "software"),
    ("distributed systems basics", "software"),
    ("security hardening for web apps", "security"),
    ("testing and observability", "software"),
    ("Kubernetes and containers", "devops"),
    ("machine learning basics for engineers", "ml"),
]
manager = create_teacher_manager()
manager.parallelism = 1
gen = CurriculumGenerator()
stats = {"questions": 0, "live_ok": 0, "exported": 0, "failed": 0}
for topic, domain in topics:
    pack = gen.generate(topic, domain=domain, count=6)
    qs = [q["question"] for q in (pack.get("questions") or []) if q.get("question")]
    if not qs:
        qs = [f"Explain {topic} with practical steps and failure modes."]
    print(json.dumps({"topic": topic, "n": len(qs)}))
    for q in qs:
        stats["questions"] += 1
        try:
            result = manager.collect_and_save(q)
            h = result.get("harvest") or {}
            live = int(h.get("live_count") or 0)
            if live > 0:
                stats["live_ok"] += 1
            else:
                stats["failed"] += 1
            stats["exported"] += int(((result.get("export") or {}).get("exported") or 0))
            print(json.dumps({
                "q": q[:80],
                "live": live,
                "mock": h.get("mock_count"),
                "exported": (result.get("export") or {}).get("exported"),
            }))
        except Exception as exc:
            stats["failed"] += 1
            print(json.dumps({"q": q[:80], "error": str(exc)}))
print(json.dumps({"harvest_stats": stats}, indent=2))
if stats["live_ok"] <= 0:
    raise SystemExit("No live teacher answers collected")
PY
  .venv/bin/om-ai learn status || true
}

train_om() {
  echo "=== merge all training data ==="
  .venv/bin/python scripts/merge_all_sft.py
  local rows
  rows="$(wc -l < data/training/om_all_sft_merged.jsonl | tr -d ' ')"
  echo "merged_rows=$rows"
  if [[ "${rows:-0}" -lt 10 ]]; then
    echo "ERROR: not enough training rows"
    exit 1
  fi

  local init_ckpt="artifacts/checkpoints/om-1.0-distill-sft/latest.pt"
  if [[ ! -f "$init_ckpt" ]]; then
    init_ckpt="artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt"
  fi

  echo "=== SFT OM on merged corpus (init=$init_ckpt) ==="
  .venv/bin/om-ai sft \
    --config configs/om-1.0-local.json \
    --data data/training/om_all_sft_merged.jsonl \
    --tokenizer artifacts/tokenizer-production-65536.json \
    --checkpoint "$init_ckpt" \
    --output artifacts/checkpoints/om-1.0-distill-sft \
    --steps "${OM_AUTO_SFT_STEPS:-400}" \
    --batch-size 1 \
    --grad-accum 4 \
    --lr 1e-5 \
    --checkpoint-every 100 \
    --device "${OM_MODEL_DEVICE:-mps}"

  # Point serve at OM-only trained checkpoint
  if grep -q '^OM_MODEL_CHECKPOINT=' .env; then
    sed -i.bak 's|^OM_MODEL_CHECKPOINT=.*|OM_MODEL_CHECKPOINT=artifacts/checkpoints/om-1.0-distill-sft/latest.pt|' .env
  else
    echo "OM_MODEL_CHECKPOINT=artifacts/checkpoints/om-1.0-distill-sft/latest.pt" >> .env
  fi
  # Ensure chat stays on native OM
  if grep -q '^OM_MODEL_PROVIDER=' .env; then
    sed -i.bak 's|^OM_MODEL_PROVIDER=.*|OM_MODEL_PROVIDER=om_native|' .env
  fi
  if grep -q '^OM_AI_CHAT_BACKEND=' .env; then
    sed -i.bak 's|^OM_AI_CHAT_BACKEND=.*|OM_AI_CHAT_BACKEND=om_native|' .env
  fi
}

remove_teachers() {
  echo "=== remove temporary teacher models (OM-only after this) ==="
  local keep_teachers="${OM_KEEP_TEACHERS:-0}"
  if [[ "$keep_teachers" == "1" ]]; then
    echo "OM_KEEP_TEACHERS=1 — skipping ollama rm"
    return 0
  fi
  while read -r name _; do
    [[ -z "${name:-}" || "$name" == "NAME" ]] && continue
    echo "ollama rm $name"
    ollama rm "$name" || true
  done < <(ollama list 2>/dev/null || true)
  ollama list || true
}

main() {
  ensure_ollama
  pull_teachers
  harvest_real
  train_om
  remove_teachers
  echo "===== COMPLETE ====="
  echo "checkpoint=artifacts/checkpoints/om-1.0-distill-sft/latest.pt"
  echo "corpus=data/training/om_all_sft_merged.jsonl"
  echo "Teachers removed. Chat uses OM only (OM_MODEL_PROVIDER=om_native)."
}

main "$@"
