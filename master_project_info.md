# OM AI Operating Brain — Master Project Info

Generated from the live repository at:

`/Users/gajendrarawat/Downloads/om-ai-operating-brain 3`

Package: **om-ai-operating-brain** · Version **0.3.0** (`pyproject.toml`)  
Python: **≥ 3.11** · CLI entry: **`om-ai`** → `om_ai.cli:main`

This file is the single map of **what this project is**, **how it is laid out**, and **where each major path lives**. It does not include secrets (`.env`), virtualenv files, Git objects, or SQLite WAL/SHM sidecars.

---

## 1. What this project is

Self-hosted **cognitive operating system** for **OM-1.0**:

- Train and run a **local decoder-only Transformer** (no Ollama / Llama proxy required on the default serve path).
- Chat UI, FastAPI, agents, memory, RAG, corpus tooling, security, evaluation.
- Default chat: `OM_MODEL_PROVIDER=om_native` + a real checkpoint under `artifacts/checkpoints/`.

**Honest limits (do not over-claim):**

- This checkout is **architecture + trainers + runtime**, not a download of trained 1B/7B/13B/70B “brains”.
- `configs/*.json` define **model shapes**, not frontier intelligence.
- Local OM-1.0 checkpoints prove the native pipeline; they are **not** ChatGPT-class weights.
- Knowledge is only as good as ingested/licensed data + retrieval. There is no infinite world knowledge without data.

---

## 2. How to run (production-shaped local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

om-ai train-om1 --config configs/om-1.0-local.json --steps 20   # optional smoke
om-ai model-info
om-ai serve --host 127.0.0.1 --port 8080
```

Workspace UI: **http://127.0.0.1:8080/chat**

Makefile: `make install` · `make test` · `make api` · `make smoke`

Docker: `Dockerfile`, `docker-compose.yml` (also `infrastructure/docker/`).

---

## 3. Default runtime path (chat)

```text
Browser  /chat  (om_ai/api/static/chat.html)
    │
    POST /api/v1/chat/completions   (om_ai/api/openai_compat.py)
    │
    om_ai/runtime/chat_backend.py
    │
    ├─ OMCognitiveBrain.process     (om_ai/core/cognitive/brain_pipeline.py)
    │       └─ run_reasoning_pipeline (om_ai/core/reasoning/pipeline.py)
    │              Intent → Technology → Plan → Retrieve → Filter → Solve
    │              → Verify → Evaluate → ResponseFormatter
    │
    ├─ OperatingIntelligence.run    (om_ai/operating_intelligence/facade.py)
    ├─ AgentBrain                   (om_ai/agent/brain.py)
    └─ OM-1.0 native generate       (om_ai/backends/om_native.py)

User bubble sees: ResponseFormatter user answer only
Debug dump (Ask / Understanding / Agents / Evaluation): OM_RESPONSE_MODE=developer
```

Related:

| Concern | Path |
|---------|------|
| User vs developer reply | `om_ai/core/response/response_formatter.py` |
| Query kind (greeting / knowledge / coding) | `om_ai/understanding/query_kind.py` |
| Knowledge filter | `om_ai/knowledge/context_filter.py` |
| Local facts (PM India, Git, React, …) | `om_ai/knowledge/facts.py` |
| ChatGPT-style UI sanitizer | `stripPipelineDump` in `om_ai/api/static/chat.html` |

---

## 4. Top-level repository structure

```text
om-ai-operating-brain 3/
├── pyproject.toml                 # package, deps, om-ai script
├── README.md
├── master_project_info.md         # this file
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── .env.example                   # env names only — copy to .env locally
├── .gitignore
├── om-ai-operating-brain.code-workspace
│
├── om_ai/                         # ★ main Python product
├── tests/                         # pytest suite (testpaths)
├── configs/                       # model + train JSON presets
├── scripts/                       # train, corpus, smoke, 70B pack
├── docs/                          # architecture, training, security, prompts
│
├── data/                          # corpora, knowledge brains, example JSONL
├── artifacts/                     # checkpoints, sqlite DBs, reports (runtime)
├── services/                      # split micro-service stubs
├── ai_platform/                   # orchestration / agent capability JSON
├── data_platform/                 # ingestion / vector store placeholders
├── training/                      # extra train configs
├── training_platform/             # evaluation placeholder
├── infrastructure/docker/         # platform Dockerfile + compose
├── security/                      # auth/encryption notes + packages
├── benchmarks/
│
├── apply_omai_chat_training_fixes.py
├── technology_engine.py           # leftover root helper (canonical is om_ai/cognition/)
├── test_*.py                      # root ad-hoc scripts (pytest uses tests/)
├── FILE_MANIFEST.txt
├── AI_70B.md
└── all_code.txt                   # dump — not the source of truth
```

**Not listed on purpose:** `.venv/`, `.git/`, `__pycache__/`, `.pytest_cache/`, `*.sqlite3-wal`, `*.sqlite3-shm`, checkpoint weight binaries.

---

## 5. `om_ai/` — full package map

Every product path that matters lives under `om_ai/`.

```text
om_ai/
├── __init__.py
├── cli.py                         # om-ai CLI
├── env.py
│
├── api/                           # FastAPI app + static UI
│   ├── main.py                    # app factory, /v1/chat, knowledge, memory
│   ├── openai_compat.py           # /api/v1/chat/completions (UI stream)
│   ├── auth_routes.py
│   ├── conversations.py
│   ├── deps.py
│   ├── foundation_routes.py
│   ├── oi_routes.py               # operating-intelligence cycle
│   ├── onboarding.py
│   ├── platform_routes.py
│   ├── platform_store.py
│   ├── workspace_routes.py
│   ├── workspace_store.py
│   └── static/
│       ├── chat.html              # ChatGPT-style workspace
│       ├── login.html
│       ├── register.html
│       └── tokens.html            # API key admin
│
├── model/                         # Transformer implementation
│   ├── transformer.py / model.py
│   ├── attention.py, rope.py, embeddings.py
│   ├── feedforward.py, normalization.py, config.py
│
├── tokenizer/                     # Byte-level BPE
│   ├── byte_bpe.py, loader.py, omai_v1.py
│
├── backends/
│   ├── om_native.py               # production chat backend
│   ├── om_registry.py, base.py, stubs.py
│
├── runtime/                       # load / generate / chat
│   ├── engine.py
│   ├── chat_backend.py            # chat_reply last-mile
│   ├── chat_orchestrator.py
│   ├── intelligence.py
│   ├── session_flags.py
│   ├── system_prompts.py
│   └── external_llms.py           # opt-in OpenAI-compatible only
│
├── core/                          # cognitive OS core
│   ├── config.py
│   ├── cognitive/brain_pipeline.py          # OMCognitiveBrain
│   ├── intent_engine/             # classifier, router, task_detector
│   ├── reasoning/
│   │   ├── pipeline.py            # run_reasoning_pipeline
│   │   ├── analyzer.py, planner.py, solver.py
│   │   ├── verifier.py, reflection.py, reasoning_chain.py
│   │   └── coding_intelligence.py
│   └── response/
│       ├── response_formatter.py  # user vs developer output
│       ├── answer_generator.py
│       ├── formatter.py, format_engine.py
│       ├── intelligence.py, quality.py
│
├── understanding/                 # language before generation
│   ├── query_kind.py
│   ├── typo_corrector.py, entities.py
│   ├── intent_detector.py, meaning_parser.py
│   ├── language_brain.py, understanding_pipeline.py
│   ├── context_engine.py, context_analyzer.py
│
├── cognition/                     # intent / tech / tasks
│   ├── intent_engine.py
│   ├── technology_engine.py
│   └── task_planner.py
│
├── cognitive/                     # goals / explanation
│   ├── goal_detector.py
│   └── explanation.py
│
├── knowledge/                     # RAG + facts + filter
│   ├── facts.py, embeddings.py, rag.py
│   ├── context_filter.py, selector.py, ranker.py
│   ├── retrieval/, ingestion/
│   ├── corpus.py, engine.py, factory.py, graph.py
│   ├── quality_filter.py, dataset_cleaner.py
│
├── knowledge_brain/               # 1600–2026 knowledge catalog
│   ├── catalog.py, corpus.py, domains.py, eras.py, directive.py
├── knowledge_universe/
│
├── memory/
│   ├── sqlite_memory.py, layers.py, session.py, conversations.py
│
├── agent/                         # chat agent controller
│   ├── brain.py, intent.py, executor.py, planner.py
│   ├── tools.py, verifier.py, useful_reply.py, coding_agent.py, context.py
│
├── agents/                        # multi-agent orchestrator
│   ├── orchestrator.py, specialists.py, roles.py, runtime.py
│
├── operating_intelligence/        # Absolute OS cycle
│   ├── facade.py
│   ├── cognition_bridge.py, knowledge_bridge.py, memory_bridge.py
│   ├── agent_bridge.py, growth_bridge.py, perception_bridge.py
│   ├── neural_simulation.py
│   └── embodiment/                # electronics, robotics, sensors, twin (stubs)
│
├── response_engine/               # markdown / stream / tone
│   ├── formatter.py, markdown_parser.py
│   ├── stream_manager.py, emotion_style.py
│
├── evaluation/                    # live + self-check
│   ├── online.py, self_checker.py
├── eval/                          # harness / benchmarks
│   ├── runner.py, benchmarks.py, platform.py
│
├── training/                      # pretrain, SFT, DPO, PPO, 70B
│   ├── trainer.py, train_om1.py, train_70b.py
│   ├── sft.py, dpo.py, ppo.py, reward_model.py, preference.py
│   ├── distributed.py, deepspeed_train.py
│   ├── dataset_loader.py, checkpoint.py, preflight.py
│
├── corpus/ + data/ + data_pipeline/
│   # import, license, PII, dedupe, shard, quality
│
├── security/                      # keys, RBAC, SSRF, audit, sessions
│   ├── auth.py, accounts.py, tokens.py, audit.py
│   ├── rate_limit.py, secrets.py, ssrf.py, session_cookie.py
│
├── live_knowledge/                # HTTP/search stubs — not another LLM
├── registry/ + checkpoint/        # model lifecycle + integrity bundles
├── discovery/                     # local project scan
├── integrations/                  # plugin SDK, HTTP, WhatsApp stub
├── multimodal/ + vision/ + voice/
├── genesis/                       # instruct template / domain generator
├── improvement/                   # weakness → queue → versions
├── continuous/                    # feedback + replay
├── conversation_engine/
├── coding_brain/
├── brain/dataset_engine.py        # dataset retrieval for solver
├── rag/relevance_checker.py
├── reasoning/                     # older reasoning engine (alongside core/)
├── foundation/ + enterprise/ + platform/ + system/ + tenancy/
├── identity/ + learning/ + observability/ + tools/
└── legacy/ollama/                 # opt-in scripts only — not serve default
```

### Package purpose (quick table)

| Area | Path | Role |
|------|------|------|
| CLI | `om_ai/cli.py` | `om-ai serve`, train, corpus, evaluate, generate |
| HTTP + UI | `om_ai/api/` | FastAPI, chat stream, login, workspace |
| Weights | `om_ai/model/` + `backends/om_native.py` | Transformer + native inference |
| Chat orchestration | `om_ai/runtime/` | Backend selection, quality gate, public reply |
| Brain pipeline | `om_ai/core/` | Intent → plan → solve → format |
| Language | `om_ai/understanding/` | Typos, entities, query kind |
| Knowledge | `om_ai/knowledge/` | Facts, embeddings, filter, RAG |
| Memory | `om_ai/memory/` | Tenant SQLite layers |
| Agents | `om_ai/agent/`, `om_ai/agents/` | Chat agent + specialist orchestrator |
| Absolute OS | `om_ai/operating_intelligence/` | Observe → think → speak → learn |
| Train | `om_ai/training/` | Pretrain / SFT / DPO / PPO / 70B |
| Security | `om_ai/security/` | Auth, audit, SSRF, rate limits |

---

## 6. Configs

| File | Use |
|------|-----|
| `configs/om-1.0-local.json` | Default local OM-1.0 shape |
| `configs/om-1.0.json` | OM-1.0 preset |
| `configs/om-tiny.json`, `tiny.json` | Tiny demo |
| `configs/om-1b.json` … `om-70b.json` | Architecture shapes (not trained brains) |
| `configs/1b.json` … `70b.json` | Same family |
| `configs/deepspeed_zero3.json` | 70B DeepSpeed |
| `configs/train_70b_gates.json` | 70B train gates |
| `configs/omai-20m.json`, `omai-50m-validate.json` | Small prove-out |

Duplicates also exist under `training/configs/`.

---

## 7. Scripts

| Path | Purpose |
|------|---------|
| `scripts/train_om1.sh`, `scripts/train_om1_mac_native.sh` | Local OM-1.0 train |
| `scripts/train_70b.sh`, `scripts/pack_for_70b_server.sh` | Cluster 70B |
| `scripts/om70b_preflight.py` | 70B preflight |
| `scripts/run_actual_training_pipeline.py` | Tiny one-shot train |
| `scripts/prepare_corpus.py`, `shard_corpus.py`, `acquire_fineweb.py` | Data |
| `scripts/train_production_tokenizer.py` | Tokenizer |
| `scripts/build_chat_sft_v4.py` | Chat SFT data |
| `scripts/smoke_test.py`, `acceptance_test.py` / `.sh` | Smoke / accept |
| `scripts/complete_chat_parity_push.sh` | Chat parity helper |

---

## 8. Tests

Pytest root: **`tests/`** (`pyproject.toml` `testpaths`).

| File | Covers |
|------|--------|
| `tests/test_response_formatter.py` | User vs developer replies; PM / React / Git / no pipeline dump |
| `tests/test_chat_web_ui.py` | `chat.html` contract + `stripPipelineDump` |
| `tests/test_chat_orchestration.py` | Cognitive brain + system prompt |
| `tests/test_chat_backend.py`, `test_chat_pipeline.py`, `test_chat_empty_generation.py` | Chat backends |
| `tests/test_os_validation.py` | Typos, PM India, Python API, embeddings |
| `tests/test_human_like_assistant.py` | Language / knowledge / slow-site reasoning |
| `tests/test_operating_intelligence.py`, `test_operating_system.py` | Absolute OS |
| `tests/test_understanding.py`, `test_agent_brain.py` | Understanding + agent |
| `tests/test_technology_pipeline.py` | React Native vs React |
| `tests/test_om_native_backend.py`, `test_no_ollama_native.py` | Native-only serve |
| `tests/test_tokenizer.py`, `test_model.py`, `test_memory.py` | Foundations |
| `tests/test_omai_corpus_v1.py`, `test_knowledge_brain.py`, `test_genesis_*.py` | Data / genesis |
| `tests/test_train_70b.py`, `test_posttraining.py`, `test_ppo.py` | Training |
| Plus accounts, workspace, platform, multimodal, live knowledge, enterprise, … |

Root `test_*.py` files (`test_intent.py`, `test_task_planner.py`, …) are **manual smoke scripts**, not the pytest suite.

---

## 9. Docs index (`docs/`)

| Doc | Topic |
|-----|--------|
| `ARCHITECTURE.md`, `CURRENT_ARCHITECTURE.md` | Layers and runtime |
| `SYSTEM_GAP_ANALYSIS.md`, `IMPLEMENTATION_ROADMAP.md` | Gaps / roadmap |
| `OM_OPERATING_SYSTEM.md` | OS framing |
| `QUICK_START.md`, `DEPLOYMENT.md`, `SECURITY.md` | Run / ship / harden |
| `TRAINING.md`, `TRAINING_1B.md` … `TRAINING_70B.md` | Train by scale |
| `SERVER_70B_HANDOFF.md`, `DISTRIBUTED_TRAINING.md` | Cluster |
| `SFT.md`, `DPO.md`, `RLHF.md` | Alignment |
| `AGENTS.md`, `MEMORY.md`, `RAG.md` | Runtime subsystems |
| `RESPONSE_EXPERIENCE.md`, `CHATGPT_PARITY_STATUS.md`, `OM_CHATGPT_GAP_ANALYSIS.md` | Chat UX |
| `OMAI_CORPUS_V1.md`, `OM_KNOWLEDGE_BRAIN_1600_2026.md`, `OM10_GENESIS_*.md` | Knowledge / genesis |
| `OWN_MODEL_MILESTONE1.md`, `OWN_INTELLIGENCE_ROADMAP.md` | Own-model path |
| `prompts/OM_AI_UNIVERSAL_KNOWLEDGE_DIRECTIVE.md` | Knowledge directive |
| `prompts/OM_AI_JARVIS_OPERATING_INTELLIGENCE.md` | Jarvis-style OS prompt |
| `prompts/OM_AI_GENESIS_PLATFORM_PRODUCTION_MASTER_PROMPT.md` | Genesis platform prompt |
| `prompts/OM10_GENESIS_UNIVERSAL_INTELLIGENCE_MASTER_DIRECTIVE.md` | OM-10 genesis directive |

---

## 10. Data (`data/`)

| Path | Contents |
|------|----------|
| `data/example_corpus.txt` | Tiny pretrain example |
| `data/example_sft.jsonl`, `example_preferences.jsonl` | Tiny SFT / DPO examples |
| `data/source_manifest.example.json` | Corpus manifest example |
| `data/omai-corpus-v1/` | OMAI-Corpus-v1 manifest + audit |
| `data/omai-genesis-v1/` | Genesis instruct manifest |
| `data/om-foundation-corpus/` | Foundation metadata shards |
| `data/om-knowledge-brain-v1/` | Eras + domain READMEs (history, CS, physics, …) |
| `data/om-knowledge-corpus/` | Domain knowledge READMEs |
| `data/om-knowledge-universe-v1/` | Universe domains (papers, patents, books, …) |
| `data/om_training/improvements/` | Improvement JSONL streams |
| `data/continuous/` | Learning cycle / recipe |

Large raw dumps (e.g. FineWeb) are **not** required in git; see `docs/EXTERNAL_ASSETS_REQUIRED.md`.

---

## 11. Artifacts (runtime, not source)

Typical local files (created by train/serve; do not commit secrets):

| Path | Role |
|------|------|
| `artifacts/checkpoints/om-1.0-long/latest.pt` | Default native weights (if trained) |
| `artifacts/tokenizer-*.json` | Tokenizers |
| `artifacts/models/om-1.0/metadata.json` | Registry metadata |
| `artifacts/om_ai.sqlite3` | App / prompts / platform |
| `artifacts/om_ai_rag.sqlite3` | RAG chunks + embeddings |
| `artifacts/knowledge.sqlite3`, `accounts.sqlite3`, `tokens.sqlite3` | KB / auth / API keys |
| `artifacts/improvement/` | Evaluator queue + versions |
| `artifacts/eval/`, `artifacts/enterprise/` | Reports |

---

## 12. Adjacent platforms (stubs / split)

```text
services/
├── api_gateway/
├── identity_service/, user_service/
├── model_service/          # gateway.py
├── knowledge_service/, retrieval_service/, memory_service/
├── agent_service/, reasoning_service/, learning_service/
├── evaluation_service/, audit_service/, billing_service/
└── model_lifecycle/

ai_platform/
├── orchestration/, workflows/, policies/, prompts/
└── agents/{coding,research,security}/capability.json

data_platform/ingestion/, data_platform/vector_store/
infrastructure/docker/
security/authentication/, security/encryption/
```

These are **supporting packages** (`pyproject.toml` includes `om_ai*`, `services*`, `ai_platform*`). The live product path is still **`om_ai` + `om-ai serve`**.

---

## 13. HTTP / UI surfaces

| URL / route | Implementation |
|-------------|----------------|
| `/chat` | `om_ai/api/static/chat.html` |
| `/login`, register | `login.html`, `register.html` |
| Tokens admin | `tokens.html` |
| `POST /v1/chat` | `om_ai/api/main.py` |
| `POST /api/v1/chat/completions` | `om_ai/api/openai_compat.py` (what the UI streams) |
| `/v1/oi/cycle` | `oi_routes.py` |
| `/v1/knowledge`, `/v1/memory` | `main.py` |
| Workspace / projects / assistants | `workspace_routes.py`, `platform_routes.py` |

---

## 14. Environment (names only)

See `.env.example`. Important keys:

- `OM_MODEL_PROVIDER=om_native`
- `OM_AI_CHAT_BACKEND=om_native`
- `OM_MODEL_CHECKPOINT` / `OM_AI_CHECKPOINT`
- `OM_MODEL_TOKENIZER` / `OM_AI_TOKENIZER`
- `OM_AI_DB`, `OM_AI_KB`, `OM_AI_TOKENS_DB`, `OM_AI_ACCOUNTS_DB`
- `OM_RESPONSE_MODE=user` (default) or `developer` for internal pipeline dump
- OpenAI-compatible chat is **opt-in** (`OM_AI_CHAT_BACKEND=openai`) — not the native default

Do not put real API keys in this markdown file.

---

## 15. Major CLI commands

| Command | Purpose |
|---------|---------|
| `om-ai serve` | FastAPI + chat UI |
| `om-ai model-info` | Native model / registry |
| `om-ai train-om1` | Local OM-1.0 train |
| `om-ai train` / `pretrain` | Causal pretrain |
| `om-ai sft` / `dpo` / `reward` | Post-training |
| `om-ai train-70b` | Cluster 70B launcher |
| `om-ai tokenizer …` | Byte-BPE |
| `om-ai corpus …` | OMAI-Corpus-v1 |
| `om-ai generate` / `chat` | Inference |
| `om-ai evaluate` / `benchmark` | Eval |
| `om-ai registry …` / `bundle` | Lifecycle |
| `om-ai project-scan` | Local project discovery |

---

## 16. Dependencies (declared)

From `pyproject.toml`: `torch`, `fastapi`, `uvicorn`, `pydantic`, `numpy`, `httpx`, `python-multipart`.  
Optional: `pytest`/`ruff` (dev), `deepspeed`, `pillow` (vision), `soundfile` (voice).

---

## 17. What “complete production chat” means in this repo

Implemented in code (not docs-only):

1. Native OM-1.0 load (no silent Ollama fallback).
2. Understanding → intent → technology → plan → retrieve → **filter** → reason → evaluate.
3. **User-facing answers** without Ask / Understanding / Agents / Evaluation dumps.
4. Chat UI that streams `/api/v1/chat/completions` and strips leftover pipeline chrome.

Still requires **you** for real product quality:

- Licensed corpus + GPU training → stronger checkpoints.
- Ingest more knowledge into RAG / fact table.
- Restart `om-ai serve` after code changes; hard-refresh `/chat`.

---

## 18. File-count note

A full recursive listing including `.venv`, Git, and binary artifacts is tens of thousands of files. This document lists **source of truth** paths: Python packages, UI, configs, scripts, tests, docs, and data layouts. For an exhaustive `find` of source only:

```bash
find om_ai tests configs scripts docs services ai_platform -type f \
  ! -path '*/__pycache__/*' | sort
```
