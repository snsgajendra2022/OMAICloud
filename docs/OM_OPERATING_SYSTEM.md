# OM Operating System — architecture, gaps, roadmap

OM is a **cognitive operating system** around locally trained checkpoints. It is not ChatGPT, does not ship OpenAI weights, private RLHF data, or a finished frontier brain.

## Required architecture (this repo)

```text
USER
  → Cognitive Understanding (intent, spelling, language, meaning, context)
  → Memory (short / long / project / preference)
  → Knowledge Brain (ingest, retrieve, rank, graph)
  → Reasoning (understand → analyze → options → decide → implement → validate)
  → Agents (coding, research, security, database, testing, deployment)
  → Response Intelligence (format, language match, highlights)
  → Evaluation (correctness, completeness, relevance, safety, quality)
  → USER
```

## What exists now (production software)

| Pillar | Status | Where |
|--------|--------|--------|
| Cognitive understanding | **Live** (heuristic) | `om_ai/understanding/`, `om_ai/cognitive/` |
| Reasoning | **Live** (heuristic + RAG + optional OM-1.0) | `om_ai/core/reasoning/` |
| Knowledge | **Live** (SQLite TF-IDF RAG, ingest, selector, ranker, JSON graph) | `om_ai/knowledge/` |
| Memory | **Live** (SQLite layers + session turn write) | `om_ai/memory/` |
| Coding intelligence | **Live** (architect blueprint: files, install, tests — not canned UI) | `om_ai/core/reasoning/coding_intelligence.py` |
| Agents | **Partial-live** (specialists emit real plans/reviews/schemas) | `om_ai/agents/specialists.py` |
| Response intelligence | **Live** | `om_ai/core/response/`, `om_ai/response_engine/` |
| Evaluation | **Live** (online 5-dimension gate + offline suite) | `om_ai/evaluation/online.py` |
| Serve path | **Live** | Absolute OS in `om_ai/operating_intelligence/facade.py` via `om-ai serve` |

Chat path: `POST /v1/chat` → `OperatingIntelligence.run` (default) → polish → stream UI.

## Honest gaps

- **Generative leap** still needs licensed data + GPU training of OM checkpoints. Layers structure answers when the tiny local model is weak.
- Retrieval is **lexical/TF-IDF**, not dense vectors by default (`docs/RAG.md`).
- Knowledge graph is JSON triples, not a production graph DB.
- Specialists produce **work products** (architecture, threat checks, schemas, test plans). They do not silently rewrite the user's disk unless an allow-listed apply path is used (`CodingAgent` dry-run default).
- Voice/vision and hardware embodiment remain gated stubs.

## Implementation roadmap

1. **Done in this pass:** identity directive; language (e.g. `creat react dahsborad`); project-mode coding blueprints; specialist agents; online eval; domain ranking; session memory writes; capability board contract.
2. **Next:** dense embeddings behind `VectorKnowledgeLayer`; auto-KG from ingest; stack-specific lint/test runners on allow-list; SSE `ui_phases` from cognitive state.
3. **Then:** attach OM-1.0 `complete_fn` to eval suite in CI; conversation summarization STM→LTM.

## Docker / APIs / tests

- Serve: `Dockerfile`, `docker-compose.yml`, `docs/DEPLOYMENT.md`.
- OS API: `GET /v1/oi/status`, `POST /v1/oi/cycle`.
- Tests: `tests/test_operating_system.py`, `tests/test_human_like_assistant.py`, `tests/test_operating_intelligence.py`.
