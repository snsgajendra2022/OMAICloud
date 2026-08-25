# OMAI-Corpus-v1 — Licensed open data for OM foundation training

OM does **not** use OpenAI/Anthropic as the brain. Training data must be
**license-approved**, cleaned, and versioned here.

## Production layout

```text
data/omai-corpus-v1/
  raw/
    fineweb/
    wikipedia/
    books/
    papers/
    code/
    conversations/
  cleaned/
  filtered/
  deduplicated/
  tokenized/
  train/
  validation/
  audit/
  manifest.json
```

## Phase-1 task checklist

| Task | Status |
|------|--------|
| Dataset downloader | ✅ `om-ai corpus fetch` |
| License tracking | ✅ catalog + JSONL metadata |
| Data validation | ✅ |
| Language filtering | ✅ |
| Quality scoring | ✅ |
| Duplicate removal | ✅ |
| PII filtering | ✅ |
| Toxic content filtering | ✅ |
| Tokenization | ✅ `tokenized/` |
| Train/validation split | ✅ |

**Data pipeline software: ~100%.**  
**TB-scale dataset inventory: still EXTERNAL (raise `--max-docs` / full dumps on big storage).**

## Commands

```bash
om-ai corpus catalog --training-only
om-ai corpus fetch --root data/omai-corpus-v1 --max-docs 40 \
  --sources wikipedia-en,gutenberg,om-owned,fineweb,open-assistant
om-ai corpus build-v1 --root data/omai-corpus-v1 --max-docs 40
om-ai train-om1 --data data/omai-corpus-v1/train/corpus.txt --steps 50
```

See also: `docs/ROADMAP_EXECUTION.md`
