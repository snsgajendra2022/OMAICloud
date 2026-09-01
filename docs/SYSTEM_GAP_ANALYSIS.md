# SYSTEM_GAP_ANALYSIS.md

Honest gap analysis. Features are **not** complete unless implemented **and** tested.

## Not in this repository (do not claim)

| Claim | Reality |
|-------|---------|
| 5-level trained weights | Architecture presets exist; useful intelligence needs licensed data + GPU training. Local OM-1.0 smoke/long checkpoints are tiny. |
| Human consciousness | Software cognition (pipelines, memory, tools). No sentience. |
| Infinite knowledge without data | Knowledge is retrieval + facts + corpora you ingest. Empty RAG ≠ world knowledge. |

## Gaps vs required OS

| Required | Gap | Priority |
|----------|-----|----------|
| Language: typos, incomplete, multilingual, intent, meaning | Lexicon + rules; Hindi/Hinglish is script/keyword detect, not full NLU | P0: expand typos + entities (PM/India); keep honest limits |
| Context: conversation, project, preferences, decisions | Exists; not every chat turn writes all layers | P0: session writer already; keep wiring |
| Knowledge: ingest, embeddings, vector search, metadata, rank | **Hashed TF-IDF vectors + cosine + BM25 already in `rag.py`**. Dense sentence-transformers not a default dependency | P0: first-class `embeddings` module + metadata search API |
| Reasoning: decompose, plan, verify, confidence, self-check | Pipeline exists; confidence not always on the cycle result | P0: expose confidence |
| Memory: short/long/project/experience | SQLite layers exist | P1: summarization STM→LTM |
| Coding: many stacks + generate/review/debug | Blueprints + dry-run agent; no silent disk rewrite | P0: Python API + React login as first-class kinds |
| Response intelligence | Formatter exists | P1: stronger language-matched rewrite |
| Evaluation | Online dims exist | P0: confidence + answered-intent flags |
| Dense GPU embeddings | Optional future; not required for production local search | P2 |

## Test debt (must pass before “complete”)

1. `creat react dahsbaord` → Create React Dashboard  
2. `create react login page` → frontend + React + login architecture  
3. `what is pm in india` → India + PM = Prime Minister  
4. `creat python api project` → backend + Python API architecture  
