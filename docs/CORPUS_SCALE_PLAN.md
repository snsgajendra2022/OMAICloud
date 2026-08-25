# Corpus Scale Plan

Goal: grow from example files to a license-governed training corpus without contaminating evals or inventing data.

## Current software

| Piece | Location |
|-------|----------|
| Manifest validation / pipeline | `om_ai/data/governance.py`, `om_ai/data/pipeline.py` |
| Corpus service (import, PII scrub, exact/near-dup, audit, shard, stats) | `om_ai/corpus/service.py` |
| CLI | `om-ai corpus …` |
| Scripts | `scripts/prepare_corpus.py`, `scripts/shard_corpus.py` |
| Example manifest | `data/source_manifest.example.json` |

## Phased plan

### Phase 0 — Dev (shipped examples)

- `data/example_corpus.txt`, tiny JSONL samples
- Purpose: unit tests + pipeline smoke only

### Phase 0.5 — OMAI-Corpus-v1 sample (implemented)

- Catalog: FineWeb, Wikipedia, Gutenberg, OpenAssistant, OM-owned (+ gated Common Crawl / Stack / arXiv)
- CLI: `om-ai corpus catalog|fetch|build-v1`
- Layout: `data/omai-corpus-v1/{raw/{fineweb,wikipedia,books,...},cleaned,filtered,deduplicated,tokenized,train,validation,audit}`
- Docs: `docs/OMAI_CORPUS_V1.md`, `docs/ROADMAP_EXECUTION.md`
- **Pipeline stages: 100%.** Sample inventory only — not trillion-token volume yet

### Phase 1 — Internal / owned

1. Declare every source in a manifest (`license`, `owner`, `allowed_for_training`)
2. `om-ai corpus validate --manifest …` / `prepare_corpus.py`
3. Import → dedupe → audit → shard
4. Hold out eval prompts; run contamination checks in `CorpusService`
5. Train tokenizer on a representative sample before full pretrain

### Phase 2 — Scale-out

- Object storage for shards; checksums in audit JSON
- Language/quality filters (heuristics today; replace with stronger LangID/quality models as needed)
- Separate SFT and preference corpora with human review workflows
- Version tags recorded in registry provenance (`training_data_version`)

### Phase 3 — Production hygiene

- Periodic re-audit; revoke sources if license changes
- Feedback replay (`om_ai/continuous/`) merged carefully with ratings thresholds
- Document retention and PII policy (`DATA_GOVERNANCE.md`)

## Scale targets (planning, not claims)

| Model class | Rough token budget (industry-typical order) | Notes |
|-------------|-----------------------------------------------|-------|
| Tiny | kilobytes–megabytes | Smoke only |
| ~1B | tens–hundreds of B tokens | Cluster recommended |
| ~7B–13B | hundreds of B+ tokens | Multi-node |
| ~70B | often trillion-token class | Multi-node, months |

Exact budgets are **your** product decision. None of those large corpora exist in-repo.

## CLI sketch

```bash
om-ai corpus import --input /data/raw --license proprietary-owned --owner om-ai
om-ai corpus dedupe --input artifacts/corpus/in.jsonl --output artifacts/corpus/deduped.jsonl
om-ai corpus audit --input artifacts/corpus/deduped.jsonl --output artifacts/corpus_audit.json
om-ai corpus shard --input artifacts/corpus/deduped.jsonl --output artifacts/shards --shard-size 10000
```
