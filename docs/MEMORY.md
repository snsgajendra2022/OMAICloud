# Memory

Module: `om_ai/memory/sqlite_memory.py` — `SQLiteMemoryStore`.

## Kinds

`conversation`, `episodic`, `semantic`, `preference`, `entity`, `task`, `tool`.

## Behavior

- Tenant + user isolation
- WAL SQLite; optional TTL via `expires_at`
- Relevance retrieval (token TF-style scoring; no external embedding API required)
- Schema migration helpers for upgrades

Default path: `artifacts/om_ai.sqlite3` (override with `OM_AI_DB`).

## API / agents

FastAPI memory endpoints and `AgentOrchestrator` can read/write the same store when wired. Memory is **persistence and retrieval**, not a substitute for model parameters — long-term “knowledge in weights” still requires training.
