# OM AI execution roadmap (ordered)

Factory path (Tesla-style): prove → small → large → mass.

```text
OMAI-20M  →  OMAI-100M  →  OMAI-1B  →  OMAI-7B  →  OMAI-70B
```

Full write-up: **`docs/OWN_INTELLIGENCE_ROADMAP.md`**

```text
Phase 0  OMAI-Corpus-v1 production pipeline     ← DONE (software)
Phase 1  Train OMAI-20M (prove owned brain)     ← NEXT
Phase 2  Grow 100M → 1B → 7B
Phase 3  OMAI-Eval + SFT/DPO chat layers
Phase 4  Memory + Tools + Agents (parallel)
Phase 5  OMAI-70B on cluster
```

## Phase 0 — Corpus pipeline (complete)

| Task | Status |
|------|--------|
| Dataset downloader | DONE (`om-ai corpus fetch`) |
| License tracking | DONE |
| Validation / lang / quality / PII / toxic | DONE |
| Dedup / tokenize / train-val split | DONE |

```bash
om-ai corpus build-v1 --root data/omai-corpus-v1 --max-docs 40
```

**Pipeline software ~100%.** Scale FineWeb/dumps for 1B+ token budgets separately.

## Phase 1 — Prove the brain (OMAI-20M)

```bash
./scripts/train_omai_20m_prove.sh
# or:
om-ai train-om1 --config configs/omai-20m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --data data/omai-corpus-v1/train/corpus.txt \
  --output artifacts/checkpoints/omai-20m-base --steps 200
```

## Later phases

- Eval: `om-ai evaluate` / `om-ai benchmark`
- Chat: `om-ai sft` / `om-ai dpo`
- Scale configs: `om-1b.json`, `om-7b.json`, `om-13b.json`, `om-70b.json`

## Honesty board

| Component | Now |
|-----------|-----|
| Software platform | ~97–100% |
| Corpus pipeline | ~100% |
| Corpus volume (100B+) | sample / EXTERNAL |
| OMAI-20M owned train | run Phase 1 |
| 1B–70B trained weights | 0% until GPU jobs |
