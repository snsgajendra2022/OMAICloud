# OM AI Own Intelligence Roadmap

Factory first. Then increase production.

```text
OMAI-20M   ← prove owned brain (tokenizer + arch + weights + train)
    ↓
OMAI-100M
    ↓
OMAI-1B
    ↓
OMAI-7B
    ↓
OMAI-70B   ← mass production (cluster)
```

No OpenAI / Claude / Llama as the brain. Only OM AI.

## Step 1 — Prove the brain (CURRENT)

Own:

| Asset | Path |
|-------|------|
| Tokenizer | `artifacts/tokenizer-production-65536.json` |
| Architecture | `configs/omai-20m.json` |
| Corpus | `data/omai-corpus-v1/` |
| Train | `om-ai train-om1 …` |
| Weights | `artifacts/checkpoints/omai-20m-base/` |

```bash
# Corpus (pipeline already complete; scale max-docs when ready)
om-ai corpus build-v1 --root data/omai-corpus-v1 --max-docs 40

# First fully owned checkpoint from OMAI-Corpus-v1
om-ai train-om1 \
  --config configs/omai-20m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --data data/omai-corpus-v1/train/corpus.txt \
  --output artifacts/checkpoints/omai-20m-base \
  --steps 200 --batch-size 4 --device mps
```

Success = `Input → OM AI → own generated output` from `omai-20m-base/latest.pt`.

## Step 2 — Grow intelligence

Scale params + tokens + GPUs: 100M → 1B → 7B. Configs under `configs/`.

## Step 3 — Brain system (parallel, even before 70B)

```text
Model + Memory + Tools + Agents + Knowledge + Code Understanding
```

A smaller model with this stack beats a large chat-only model.

## Step 4 — OMAI-70B

Own weights, tokenizer, dataset, training code, inference, deploy — on cluster compute.

## Honesty

| Piece | Status |
|-------|--------|
| Software factory | ~97–100% |
| Corpus pipeline | ~100% (volume still sample until scaled dumps) |
| OMAI-20M owned checkpoint | train with command above |
| 1B–70B | engineering + compute after 20M proof |

See also: `docs/OMAI_CORPUS_V1.md`, `docs/ROADMAP_EXECUTION.md`
