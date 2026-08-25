# OM AI Own Model — Completion Tracker

Milestone 1 target: **OMAI-Corpus-v1 + first own weights** (no third-party LLM brain).

```text
Data → Tokenizer → Training → Checkpoint → Inference → OM AI answers
```

## Tracker

| Component | Status | Notes |
|-----------|--------|-------|
| OM Software Platform | **~97%** | Serve, agents, API |
| Tokenizer (chat specials) | **~85%** | Production 65k; `<\|code\|>` etc. planned |
| Corpus Pipeline | **~95%** | `om_ai/data_pipeline/` + `data/omai-corpus-v1/` |
| OMAI-20M train path | **~80%** | Config + train-om1 + prove script |
| First own checkpoint | **run train** | `artifacts/checkpoints/omai-20m-base/` |
| 1B / 7B / 70B | **0%** | After 20M proof + compute |

## Factory layout (in-repo)

| Roadmap name | OM path |
|--------------|---------|
| `om-ai-corpus-v1/` | `data/omai-corpus-v1/` |
| `data_pipeline/` | `om_ai/data_pipeline/` |
| `om-ai-model/` | `om_ai/model/` |
| `om-ai-training/` | `om_ai/training/` |
| `om-ai-inference/` | `om_ai/runtime/` (`om-ai generate`) |
| `om-ai-evaluation/` | `om_ai/eval/` |

## Commands

```bash
# Phase 1–2 corpus factory
om-ai data-pipeline run --root data/omai-corpus-v1 --max-docs 40
om-ai data-pipeline validate
om-ai data-pipeline tokenizer-status

# Phase 5–8: train + infer (owned brain)
./scripts/train_omai_20m_prove.sh
om-ai generate --config configs/omai-20m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/omai-20m-base/latest.pt \
  --prompt "Explain Python" --max-new-tokens 40
```

## Scale path

```text
OMAI-20M → OMAI-100M → OMAI-1B → OMAI-7B → OMAI-70B
```

See `docs/OWN_INTELLIGENCE_ROADMAP.md`.
