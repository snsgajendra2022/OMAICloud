#!/usr/bin/env bash
# Complete local OM chat push: SFT → DPO → point serve at new checkpoint.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3)"

export OM_AI_CONFIG=configs/om-1.0-local.json
export OM_AI_TOKENIZER=artifacts/tokenizer-production-65536.json
CFG=configs/om-1.0-local.json
TOK=artifacts/tokenizer-production-65536.json
BASE=artifacts/checkpoints/om-1.0-chat-sft/latest.pt
OUT_SFT=artifacts/checkpoints/om-1.0-chat-sft-v4
OUT_DPO=artifacts/checkpoints/om-1.0-chat-dpo-v4
DATA=data/om-chat-sft-v4-complete.jsonl
PREF=data/om-chat-dpo-v4.jsonl

"$PY" scripts/build_chat_sft_v4.py
# refresh preference file
"$PY" - <<'PY'
import json, random
from pathlib import Path
src = Path("data/om-chat-sft-v4-complete.jsonl")
out = Path("data/om-chat-dpo-v4.jsonl")
rng = random.Random(7)
bad = [
 "As an AI language model I cannot help.",
 "I am ChatGPT created by OpenAI.",
 "Sorry I don't understand anything.",
 "......",
 "lol idk",
]
n=0
with src.open() as f, out.open("w") as g:
    for line in f:
        try: row=json.loads(line)
        except Exception: continue
        if "messages" in row:
            msgs=row["messages"]
            user=next((m["content"] for m in msgs if m.get("role")=="user"), None)
            chosen=next((m["content"] for m in reversed(msgs) if m.get("role")=="assistant"), None)
            if not user or not chosen: continue
            prompt=user
        else:
            prompt=row.get("prompt") or ""
            chosen=row.get("response") or ""
            if not prompt or not chosen: continue
        g.write(json.dumps({"prompt":prompt,"chosen":chosen,"rejected":rng.choice(bad)},ensure_ascii=False)+"\n")
        n+=1
        if n>=1500: break
print("dpo", n)
PY

mkdir -p "$OUT_SFT" "$OUT_DPO"
echo "[1/2] SFT..."
"$PY" -m om_ai.cli sft --config "$CFG" --tokenizer "$TOK" --checkpoint "$BASE" \
  --data "$DATA" --steps "${OM_SFT_STEPS:-4000}" --batch-size 2 --grad-accum 4 \
  --lr 2e-5 --precision fp32 --device "${OM_DEVICE:-cpu}" --output "$OUT_SFT" --checkpoint-every 500

CKPT="$OUT_SFT/latest.pt"
echo "[2/2] DPO..."
"$PY" -m om_ai.cli dpo --config "$CFG" --tokenizer "$TOK" --checkpoint "$CKPT" \
  --data "$PREF" --steps "${OM_DPO_STEPS:-800}" --batch-size 1 --lr 1e-6 --beta 0.1 \
  --device "${OM_DEVICE:-cpu}" --output "$OUT_DPO"

# Point default checkpoint to DPO candidate
python3 - <<PY
from pathlib import Path
env = Path(".env")
text = env.read_text()
new = "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt"
for key in ("OM_AI_CHECKPOINT=", "OM_MODEL_CHECKPOINT="):
    lines=[]
    for line in text.splitlines():
        if line.startswith(key):
            lines.append(key+new)
        else:
            lines.append(line)
    text="\n".join(lines)+"\n"
env.write_text(text)
print("env ->", new)
PY

"$PY" - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone
st={
  "stage":"CHAT_PARITY_PUSH_V4",
  "updated_at":datetime.now(timezone.utc).isoformat(),
  "sft_data":"data/om-chat-sft-v4-complete.jsonl",
  "dpo_data":"data/om-chat-dpo-v4.jsonl",
  "sft_ckpt":"artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt",
  "dpo_ckpt":"artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt",
  "config":"configs/om-1.0-local.json",
  "max_seq_len":256,
  "note":"Local ~20M push only. ChatGPT-class still needs 1B–70B GPU training.",
  "chatgpt_intelligence_claim": False,
}
Path("artifacts/OM_CHAT_PARITY_PUSH_V4.json").write_text(json.dumps(st,indent=2))
print(json.dumps(st,indent=2))
PY
echo "DONE"
