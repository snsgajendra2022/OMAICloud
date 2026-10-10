# Apple M4 Local Training (48 GB+ Unified Memory)

This runbook is for pipeline validation and small native OM experiments. It does not promise ChatGPT or cloud-frontier parity.

## 1. Update and inspect the branch

```bash
git switch feature/gpt5-production-runtime
git pull --ff-only
git status --short
system_profiler SPHardwareDataType
df -h .
```

Preserve local changes before pulling. Use ARM64 Python 3.11+.

## 2. Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Verify Apple GPU support:

```bash
python - <<'PY'
import platform, torch
print("arch:", platform.machine())
print("torch:", torch.__version__)
print("MPS built:", torch.backends.mps.is_built())
print("MPS available:", torch.backends.mps.is_available())
if torch.backends.mps.is_available():
    print("MPS recommended working set GiB:",
          round(torch.mps.recommended_max_memory() / 1024**3, 2))
    x = torch.ones((2, 2), device="mps")
    print("MPS smoke:", (x @ x).tolist())
PY
```

Do not start training if MPS is expected but unavailable; resolve the environment first.

## 3. Inspect supported commands and the model estimate

```bash
om-ai train --help
om-ai tokenizer train --help
om-ai model-info --config configs/om-m4-48gb.json
python scripts/diagnose_native_chat.py
python scripts/evaluate_om_capabilities.py
```

Save the baseline output before changing weights.

## 4. Prepare approved corpus and tokenizer

Review `data/source_manifest.example.json`. Only list sources with verified rights and set training approval truthfully.

```bash
python scripts/prepare_corpus.py \
  --manifest data/source_manifest.example.json \
  --output artifacts/corpus.jsonl \
  --audit artifacts/corpus_audit.json

om-ai tokenizer train \
  --input artifacts/corpus.jsonl \
  --output artifacts/tokenizer-m4-2048.json \
  --vocab-size 2048

om-ai tokenizer inspect --tokenizer artifacts/tokenizer-m4-2048.json
```

Ensure the actual tokenizer vocabulary is compatible with the config. If vocabulary size differs, adjust the config intentionally before training; do not reuse incompatible checkpoints.

## 5. Short FP32 smoke test

```bash
mkdir -p artifacts/m4-smoke
om-ai train \
  --config configs/om-m4-48gb.json \
  --data artifacts/corpus.jsonl \
  --tokenizer artifacts/tokenizer-m4-2048.json \
  --device mps \
  --steps 20 \
  --batch-size 1 \
  --grad-accum 8 \
  --precision fp32 \
  --gradient-checkpointing \
  --checkpoint-every 10 \
  --log-every 1 \
  --output artifacts/m4-smoke
```

This profile is a small experiment, roughly in the low tens of millions of parameters according to the repo's estimator, not a production assistant. Confirm finite loss, successful checkpoint save, and checkpoint reload before increasing steps.

## 6. Longer experiment, only after smoke-test success

```bash
om-ai train \
  --config configs/om-m4-48gb.json \
  --data artifacts/corpus.jsonl \
  --tokenizer artifacts/tokenizer-m4-2048.json \
  --device mps \
  --steps 1000 \
  --batch-size 1 \
  --grad-accum 8 \
  --precision auto \
  --gradient-checkpointing \
  --checkpoint-every 100 \
  --log-every 10 \
  --output artifacts/m4-pretrain
```

The current trainer selects FP16 autocast for `precision=auto` on MPS. If the run has non-finite loss or unsupported operations, return to FP32. Record memory, tokens/second, final and held-out loss, tokenizer/config hashes, and checkpoint reload status.

## Memory and evaluation rules

- Start with context length 512 and micro-batch 1; change only one setting at a time.
- Gradient accumulation improves effective batch size but does not remove the memory cost of optimizer states.
- Keep enough free disk for checkpoints and avoid leaving memory-heavy applications open.
- Do not use the 1B/7B/13B/70B configs for full-parameter pretraining on this machine without measured evidence of feasibility.
- Keep held-out data separate. Run diagnostics and capability evaluation again after training and compare with the saved baseline.
- Training loss alone is not proof of assistant quality. Do not claim cloud-level parity without reproducible benchmarks.
