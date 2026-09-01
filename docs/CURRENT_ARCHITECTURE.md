# CURRENT_ARCHITECTURE.md

Status: OM AI Operating Brain **v0.3** as of 2026-09-01.

OM is a **self-hosted cognitive operating system**: FastAPI + SQLite + local OM checkpoints. It does **not** call OpenAI/Anthropic/Google model APIs.

## Runtime path

```text
om-ai serve → FastAPI (om_ai/api)
                 │
                 ├─ POST /v1/chat  → chat_backend
                 │                      ├─ OperatingIntelligence.run (default)
                 │                      └─ AgentBrain + OM-1.0 native generate
                 ├─ POST /v1/oi/cycle
                 ├─ /v1/knowledge, /v1/memory, /v1/agent/goal
                 └─ workspace UI  /chat
```

Absolute OS cycle: Observe → Understand → Remember → Research → Think → Agents → Verify → Speak → Evaluate → Learn.

## Layers that exist in code

| Layer | Package | Mechanism |
|-------|---------|-----------|
| Language / meaning | `om_ai/understanding/` | Typo lexicon, grammar rewrite, language tag, token gloss, canonical task |
| Context / goals | `om_ai/cognitive/`, `context_analyzer.py` | Follow-up resolution, project topic, audience |
| Reasoning | `om_ai/core/reasoning/` | Analyze → plan → solve (RAG/dataset/model) → verify → reflect |
| Knowledge | `om_ai/knowledge/` | Ingest → chunk → **hashed TF-IDF embeddings in SQLite** → cosine + BM25 hybrid search → selector/ranker |
| Memory | `om_ai/memory/` | SQLite kinds + LayeredMemory (short, conversation, user, project, experience, skill) |
| Coding | `coding_intelligence.py`, `coding_brain`, `CodingAgent` | Architecture / files / install / tests; dry-run repo map |
| Agents | `om_ai/agents/specialists.py` | Coding, research, security, database, testing, deployment work products |
| Response | `om_ai/core/response/`, `response_engine/` | Format, markdown, highlights, quality repair |
| Evaluation | `om_ai/evaluation/online.py` | Live dimension scores |
| Model | `om_ai/model/`, `backends/om_native.py` | Decoder-only Transformer; local checkpoint only |

## Data stores

- `artifacts/om_ai.sqlite3` — app, prompts, platform
- `artifacts/om_ai_rag.sqlite3` — RAG chunks + embedding BLOBs
- Memory / audit / tokens DBs per env (`.env.example`)

## Docker

`Dockerfile` + `docker-compose.yml` serve port 8080 with `artifacts` mounted. See `docs/DEPLOYMENT.md`.

## What this architecture is not

- Not ChatGPT weights or OpenAI private data
- Not a 5-level trained frontier brain in this checkout
- Not human consciousness
- Not infinite knowledge without ingested/licensed data
