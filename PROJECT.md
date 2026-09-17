# OM AI Operating Brain — Full Project Reference

> **Version:** 0.3.0  
> **Package:** `om-ai-operating-brain` (`pyproject.toml`)  
> **CLI entry:** `om-ai` → `om_ai.cli:main`  
> **Default serve:** `http://127.0.0.1:8080`  
> **Generated as:** master map of structure, flows, APIs, and file roles

This document is the **single full-project reference**: architecture flows, every HTTP API, directory layout, runtime/data paths, and a package-by-package file inventory (~942 Python modules under `om_ai/`).

Related deep-dives live under `docs/` (see §16). This file does **not** claim trained frontier weights ship in the repo.

---

## Table of contents

1. [What this project is](#1-what-this-project-is)
2. [Repository layout (top level)](#2-repository-layout-top-level)
3. [End-to-end system flows](#3-end-to-end-system-flows)
4. [Runtime / chat pipeline](#4-runtime--chat-pipeline)
5. [Training & distillation flows](#5-training--distillation-flows)
6. [External LLMs (OpenRouter & teachers)](#6-external-llms-openrouter--teachers)
7. [HTTP API catalog (complete)](#7-http-api-catalog-complete)
8. [UI surfaces](#8-ui-surfaces)
9. [CLI commands](#9-cli-commands)
10. [Configs, env, artifacts, data paths](#10-configs-env-artifacts-data-paths)
11. [Services & infrastructure](#11-services--infrastructure)
12. [Security & auth model](#12-security--auth-model)
13. [Core functionality by domain](#13-core-functionality-by-domain)
14. [Complete `om_ai/` package & file inventory](#14-complete-om_ai-package--file-inventory)
15. [Tests, scripts, docs index](#15-tests-scripts-docs-index)
16. [Honesty / boundaries](#16-honesty--boundaries)

---

## 1. What this project is

**OM AI Operating Brain** is a self-hosted cognitive platform:

| Layer | Purpose |
|-------|---------|
| **Model** | From-scratch decoder-only Transformer (`om_ai/model/`) |
| **Tokenizer** | Byte-level BPE (`om_ai/tokenizer/`) |
| **Training** | Pretrain → SFT → reward → DPO/PPO (`om_ai/training/`) |
| **Runtime** | Local inference engine + chat orchestrator (`om_ai/runtime/`) |
| **API** | FastAPI server + OpenAI-compatible shim (`om_ai/api/`) |
| **Workspace UI** | Chat / login / tokens HTML (`om_ai/api/static/`) |
| **Memory / RAG** | SQLite memory + persistent knowledge (`om_ai/memory/`, `om_ai/knowledge/`) |
| **Agents** | Plan → tools → verify (`om_ai/agents/`, `om_ai/actions/`) |
| **Distillation** | Multi-LLM teacher harvest → SFT/DPO export (`om_ai/core/distillation/`) |
| **Security** | API keys, accounts/sessions, RBAC, SSRF, audit, rate limits |

Default production chat path: **OM-1.0 native** (`OM_MODEL_PROVIDER=om_native`). External providers (OpenRouter, GPT, Claude, …) are **optional** and only run when enabled + keyed.

---

## 2. Repository layout (top level)

```text
om-ai-operating-brain 3/
├── om_ai/                 # Main Python package (~942 .py files)
├── services/              # Microservice-style packages (gateway, model, memory, …)
├── ai_platform/           # Platform glue package
├── configs/               # Model architecture / train JSON presets
├── data/                  # Corpora, knowledge brains, distillation, SFT/DPO
├── artifacts/             # Checkpoints, SQLite DBs, registry, uploads (runtime)
├── docs/                  # Architecture / training / security docs
├── tests/                 # Pytest suite
├── scripts/               # Train / pack / ops shell+python helpers
├── infrastructure/        # Docker / k8s / terraform / monitoring
├── training/              # Training assets layout (datasets, scripts, eval)
├── training_platform/     # Dataset / eval / model_registry scaffolding
├── data_platform/         # Ingestion / embeddings / vector_store scaffolding
├── security/              # Top-level security scaffolding
├── benchmarks/            # Benchmark fixtures
├── om_production/         # Production matrix / dataset builders
├── storage/               # Local storage stubs
├── logs/                  # Runtime logs
├── pyproject.toml         # Package metadata + `om-ai` console script
├── README.md              # Quick start
├── .env.example           # Env template
├── Dockerfile / docker-compose.yml
└── PROJECT.md             # ← this file
```

---

## 3. End-to-end system flows

### 3.1 Serve → Chat (user message)

```text
Browser / SDK
    │  GET /chat  (static chat.html)
    │  POST /api/v1/chat/completions   or   POST /v1/chat
    ▼
om_ai/api/main.py  (+ openai_compat / platform / conversations routers)
    │  require_auth / rate_limit / audit
    ▼
om_ai/runtime/chat_backend.py   resolve backend
    ├─ om_native  → om_ai/backends/om_native.py → LocalLLMEngine → OMTransformer
    ├─ openai / external → om_ai/runtime/external_llms.py (OpenRouter, GPT, …)
    └─ local engine fallback (configured)
    │
    ├─ optional: memory inject (om_ai/memory/)
    ├─ optional: RAG (om_ai/knowledge/)
    ├─ optional: live_knowledge (HTTP/search)
    ├─ optional: agents / tools
    └─ response_engine formatting / streaming
    ▼
JSON or SSE stream → UI / client
```

### 3.2 Auth → Workspace bootstrap

```text
GET /login|/register → static HTML
POST /v1/auth/register|/login → session cookie / token (om_ai/security/accounts.py)
GET  /v1/auth/me
POST /v1/workspace/bootstrap → workspaces + default conversation
CRUD /v1/conversations, /v1/projects, /v1/settings, …
```

### 3.3 Corpus → Train → Registry → Serve

```text
data/* corpora
    │  om-ai corpus … / data_engine / knowledge_brain
    ▼
tokenizer train → artifacts/tokenizer-*.json
    ▼
om-ai train / train-om1 / sft / dpo
    ▼
artifacts/checkpoints/*/latest.pt
    ▼
om_ai/registry + artifacts/models/om-1.0/
    ▼
OM_MODEL_CHECKPOINT=…  +  om-ai serve
```

### 3.4 Teacher distillation (improve OM with API teachers)

```text
Task / curriculum question
    ▼
om_ai/tools/llm_harvest.py  OR  TeacherManager
    ▼
LLMHarvester → external_llms (openrouter/gpt/claude/…)  [outputs only]
    ▼
normalize → compare → rank → TrainingExporter
    ▼
data/om_distillation/*.jsonl  (SFT / DPO pairs)
    ▼
om-ai sft / dpo → stronger OM checkpoint
```

**Legal rule:** use only API outputs from models that allow distillation (OpenRouter `distillable=true` / `enforce_distillable_text`). Never expect private training corpora or weights from OpenRouter.

---

## 4. Runtime / chat pipeline

| File | Role |
|------|------|
| `om_ai/runtime/engine.py` | `LocalLLMEngine` load/generate |
| `om_ai/runtime/chat_backend.py` | Backend resolution + chat reply |
| `om_ai/runtime/chat_orchestrator.py` | Higher-level chat orchestration |
| `om_ai/runtime/chat_pipeline.py` | Pipeline stages |
| `om_ai/runtime/external_llms.py` | External provider catalog + HTTP chat |
| `om_ai/runtime/evolution_matrix.py` | OM-L1…L5 matrix labels |
| `om_ai/runtime/live_answer.py` | Live answer helpers |
| `om_ai/runtime/public_reply.py` | Public-facing reply shaping |
| `om_ai/runtime/system_prompts.py` | System prompt templates |
| `om_ai/backends/om_native.py` | OM-1.0 native backend |
| `om_ai/backends/base.py` | Backend protocol / errors |
| `om_ai/model/transformer.py` | Core Transformer |
| `om_ai/tokenizer/byte_bpe.py` | Tokenizer |

**UI chat stack:** `om_ai/api/static/chat.html` talks to `/api/v1/chat/completions`, `/v1/conversations*`, `/v1/settings`, `/v1/models/catalog`, projects, memories, tools, multimodal upload endpoints.

---

## 5. Training & distillation flows

| Stage | CLI / module | Typical I/O |
|-------|--------------|-------------|
| Tokenizer | `om-ai tokenizer train` | `data/…` → `artifacts/tokenizer*.json` |
| Pretrain | `om-ai train` / `train-om1` | corpus + tokenizer → `artifacts/checkpoints/` |
| SFT | `om-ai sft` / `om_ai/training/sft.py` | instruction JSONL → chat checkpoint |
| Reward | `om-ai reward` | preference data → reward model |
| DPO | `om-ai dpo` | chosen/rejected pairs → aligned checkpoint |
| PPO | `om_ai/training/ppo.py` | RL loop infra |
| 70B | `om-ai train-70b` + DeepSpeed | Mac prep → CUDA server (`docs/SERVER_70B_HANDOFF.md`) |
| Distill harvest | `python -m om_ai.tools.llm_harvest` | teacher APIs → `data/om_distillation/` |
| Eval | `om-ai evaluate` / `benchmark` | `benchmarks/`, `artifacts/eval/` |

**Distillation package (STEP 94):** `om_ai/core/distillation/` — `TeacherManager`, `LLMHarvester`, `DatasetBuilder`, `TrainingExporter`, `ContinuousDistillationLoop`, schedulers, provenance, quality rankers.

---

## 6. External LLMs (OpenRouter & teachers)

Defined in `om_ai/runtime/external_llms.py` → `LLM_CATALOG`:

| Provider id | Vendor | Style | Env keys (examples) |
|-------------|--------|-------|---------------------|
| `om` | OM AI | om_native | (owned) |
| `gpt` | OpenAI | openai | `OPENAI_API_KEY` |
| `claude` | Anthropic | anthropic | `ANTHROPIC_API_KEY` |
| `gemini` | Google | openai-compat | `GEMINI_API_KEY` |
| `llama` | Meta via Groq | openai | `GROQ_API_KEY` |
| `mistral` | Mistral | openai | `MISTRAL_API_KEY` |
| `qwen` | Alibaba | openai | `DASHSCOPE_API_KEY` |
| `deepseek` | DeepSeek | openai | `DEEPSEEK_API_KEY` |
| `openrouter` | OpenRouter | openai | `OPENROUTER_API_KEY` / `OM_AI_OPENROUTER_API_KEY` |
| `grok` | xAI | openai | `XAI_API_KEY` |

OpenRouter defaults: `base_url=https://openrouter.ai/api/v1`, model `openrouter/auto` (override with `OPENROUTER_MODEL`).

Enable in UI **Settings → AI** (`PATCH /v1/settings` → `llm_providers.openrouter=true`) and store key, or set env.

Harvest example:

```bash
.venv/bin/python -m om_ai.tools.llm_harvest \
  --task "Explain Kubernetes architecture" \
  --teachers openrouter \
  --out data/om_distillation/ \
  --no-mock
```

---

## 7. HTTP API catalog (complete)

Base URL: `http://127.0.0.1:8080`  
Auth: API key / session (see §12). OpenAPI interactive docs: `/docs`.

### 7.1 System & UI

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | `main.py` |
| GET | `/ready` | `main.py` |
| GET | `/` | `main.py` |
| GET | `/login` | `main.py` → `static/login.html` |
| GET | `/register` | `main.py` → `static/register.html` |
| GET | `/chat`, `/ui/chat` | `main.py` → `static/chat.html` |
| GET | `/tokens`, `/ui/tokens` | `main.py` → `static/tokens.html` |
| GET | `/ui/settings` | `main.py` |
| GET | `/static/*` | StaticFiles mount |

### 7.2 Auth (`auth_routes.py`)

| Method | Path |
|--------|------|
| GET | `/v1/auth/status` |
| POST | `/v1/auth/register` |
| POST | `/v1/auth/login` |
| POST | `/v1/auth/logout` |
| POST | `/v1/auth/logout-all` |
| GET | `/v1/auth/me` |

### 7.3 OpenAI-compatible (`openai_compat.py`, prefix `/api/v1`)

| Method | Path |
|--------|------|
| GET | `/api/v1/models` |
| GET | `/api/v1/chat/backend` |
| POST | `/api/v1/chat/completions` |
| POST | `/api/v1/completions` |

### 7.4 Core inference / memory / knowledge / agent (`main.py`)

| Method | Path |
|--------|------|
| POST | `/v1/model/load` |
| GET | `/v1/model/info` |
| GET | `/api/v1/model` |
| POST | `/v1/generate` |
| POST | `/v1/generate/stream` |
| POST | `/v1/chat` |
| POST | `/v1/memory` |
| GET | `/v1/memory/{tenant}/{user}` |
| POST | `/v1/knowledge` |
| POST | `/v1/knowledge/ingest` |
| GET | `/v1/knowledge/search` |
| POST | `/v1/agent/goal` |
| GET | `/v1/agent/tools` |
| POST | `/v1/feedback` |
| GET | `/v1/registry` |
| POST | `/v1/multimodal` |
| POST | `/v1/multimodal/analyze` |

### 7.5 API tokens (`main.py`)

| Method | Path |
|--------|------|
| GET | `/v1/tokens/meta` |
| POST | `/v1/tokens` |
| GET | `/v1/tokens` |
| DELETE | `/v1/tokens/{token_id}` |

### 7.6 Conversations & folders (`conversations.py`)

| Method | Path |
|--------|------|
| GET/POST | `/v1/conversations` |
| GET/PATCH/DELETE | `/v1/conversations/{conversation_id}` |
| GET | `/v1/conversations/{conversation_id}/export` |
| POST/DELETE | `/v1/conversations/{conversation_id}/share` |
| GET | `/share/{share_token}` |
| POST | `/v1/conversations/{conversation_id}/messages` |
| POST | `/v1/conversations/{conversation_id}/feedback` |
| GET/POST | `/v1/folders` |
| PATCH/DELETE | `/v1/folders/{folder_id}` |
| GET/PUT | `/v1/profile` |

### 7.7 Platform workspace features (`platform_routes.py`)

| Method | Path |
|--------|------|
| GET/POST | `/v1/workspaces` |
| POST | `/v1/workspace/bootstrap` |
| GET | `/v1/search` |
| GET/POST | `/v1/files` |
| GET/PATCH/DELETE | `/v1/files/{file_id}` |
| GET/POST | `/v1/library` |
| DELETE | `/v1/library/{item_id}` |
| PATCH | `/v1/library/{item_id}/favorite` |
| GET/POST | `/v1/prompts` |
| PATCH/DELETE | `/v1/prompts/{prompt_id}` |
| GET/POST | `/v1/tasks` |
| PATCH/DELETE | `/v1/tasks/{task_id}` |
| GET | `/v1/notifications` |
| POST | `/v1/notifications/{notif_id}/read` |
| GET/PATCH | `/v1/settings` |
| GET/POST | `/v1/knowledge/sources` |
| DELETE | `/v1/knowledge/sources/{source_id}` |
| GET | `/v1/explore` |
| POST | `/v1/explore/{item_id}/use` |
| GET/POST | `/v1/memories` |
| PATCH/DELETE | `/v1/memories/{memory_id}` |
| GET | `/v1/models/catalog` |
| GET | `/v1/history` |
| GET | `/v1/profile/me` |
| GET | `/v1/tools` |
| PATCH | `/v1/tools/{tool_id}` |
| GET/POST | `/v1/scheduled-tasks` |
| GET/POST | `/v1/projects/{project_id}/members` |
| DELETE | `/v1/projects/{project_id}/members/{member_id}` |
| GET/POST | `/v1/instructions/versions` |
| GET | `/v1/billing` |

### 7.8 Projects & assistants (`workspace_routes.py`)

Dual-prefixed many routes as `/v1/...` and `/api/...`.

| Area | Paths |
|------|-------|
| Projects CRUD | `/v1/projects`, `/v1/projects/{id}`, duplicate |
| Project chats | `/v1/projects/{id}/chats` |
| Project files | `/v1/projects/{id}/files` |
| Project memory | `/v1/projects/{id}/memory` |
| Project knowledge | `/v1/projects/{id}/knowledge` |
| Assistants | `/v1/assistants`, duplicate, PATCH/DELETE |
| System prompts | `/v1/system-prompts` |

### 7.9 Operating Intelligence (`oi_routes.py`, prefix `/v1/oi`)

| Method | Path |
|--------|------|
| GET | `/v1/oi/status` |
| POST | `/v1/oi/cycle` |
| POST | `/v1/oi/hardware/command` |
| POST | `/v1/oi/sensors/ingest` |

### 7.10 Foundation (`foundation_routes.py`)

| Method | Path |
|--------|------|
| POST | `/api/knowledge/search` |
| POST | `/api/knowledge/upload` |
| POST | `/api/reasoning/analyze` |
| POST | `/api/evaluation/run` |
| POST | `/api/learning/feedback` |
| POST | `/api/learning/export` |

### 7.11 Full route table (machine-extracted)

| Path | Method | File |
|------|--------|------|
| `/v1/auth/status` | GET | `auth_routes.py` |
| `/v1/auth/register` | POST | `auth_routes.py` |
| `/v1/auth/login` | POST | `auth_routes.py` |
| `/v1/auth/logout` | POST | `auth_routes.py` |
| `/v1/auth/logout-all` | POST | `auth_routes.py` |
| `/v1/auth/me` | GET | `auth_routes.py` |
| `/v1/conversations` | GET | `conversations.py` |
| `/v1/conversations` | POST | `conversations.py` |
| `/v1/conversations/{conversation_id}` | GET | `conversations.py` |
| `/v1/conversations/{conversation_id}` | PATCH | `conversations.py` |
| `/v1/conversations/{conversation_id}` | DELETE | `conversations.py` |
| `/v1/conversations/{conversation_id}/export` | GET | `conversations.py` |
| `/v1/conversations/{conversation_id}/share` | POST | `conversations.py` |
| `/v1/conversations/{conversation_id}/share` | DELETE | `conversations.py` |
| `/share/{share_token}` | GET | `conversations.py` |
| `/v1/conversations/{conversation_id}/messages` | POST | `conversations.py` |
| `/v1/conversations/{conversation_id}/feedback` | POST | `conversations.py` |
| `/v1/folders` | GET | `conversations.py` |
| `/v1/folders` | POST | `conversations.py` |
| `/v1/folders/{folder_id}` | PATCH | `conversations.py` |
| `/v1/folders/{folder_id}` | DELETE | `conversations.py` |
| `/v1/profile` | GET | `conversations.py` |
| `/v1/profile` | PUT | `conversations.py` |
| `/api/knowledge/search` | POST | `foundation_routes.py` |
| `/api/knowledge/upload` | POST | `foundation_routes.py` |
| `/api/reasoning/analyze` | POST | `foundation_routes.py` |
| `/api/evaluation/run` | POST | `foundation_routes.py` |
| `/api/learning/feedback` | POST | `foundation_routes.py` |
| `/api/learning/export` | POST | `foundation_routes.py` |
| `/health` | GET | `main.py` |
| `/ready` | GET | `main.py` |
| `/v1/model/load` | POST | `main.py` |
| `/v1/model/info` | GET | `main.py` |
| `/api/v1/model` | GET | `main.py` |
| `/v1/generate` | POST | `main.py` |
| `/v1/generate/stream` | POST | `main.py` |
| `/v1/chat` | POST | `main.py` |
| `/v1/memory` | POST | `main.py` |
| `/v1/memory/{tenant}/{user}` | GET | `main.py` |
| `/v1/knowledge` | POST | `main.py` |
| `/v1/knowledge/ingest` | POST | `main.py` |
| `/v1/knowledge/search` | GET | `main.py` |
| `/v1/agent/goal` | POST | `main.py` |
| `/v1/agent/tools` | GET | `main.py` |
| `/v1/feedback` | POST | `main.py` |
| `/v1/registry` | GET | `main.py` |
| `/.well-known/appspecific/com.chrome.devtools.json` | GET | `main.py` |
| `/` | GET | `main.py` |
| `/login` | GET | `main.py` |
| `/register` | GET | `main.py` |
| `/chat` | GET | `main.py` |
| `/ui/chat` | GET | `main.py` |
| `/ui/tokens` | GET | `main.py` |
| `/tokens` | GET | `main.py` |
| `/ui/settings` | GET | `main.py` |
| `/v1/tokens/meta` | GET | `main.py` |
| `/v1/tokens` | POST | `main.py` |
| `/v1/tokens` | GET | `main.py` |
| `/v1/tokens/{token_id}` | DELETE | `main.py` |
| `/v1/multimodal` | POST | `main.py` |
| `/v1/multimodal/analyze` | POST | `main.py` |
| `/v1/oi/status` | GET | `oi_routes.py` |
| `/v1/oi/cycle` | POST | `oi_routes.py` |
| `/v1/oi/hardware/command` | POST | `oi_routes.py` |
| `/v1/oi/sensors/ingest` | POST | `oi_routes.py` |
| `/api/v1/chat/backend` | GET | `openai_compat.py` |
| `/api/v1/models` | GET | `openai_compat.py` |
| `/api/v1/chat/completions` | POST | `openai_compat.py` |
| `/api/v1/completions` | POST | `openai_compat.py` |
| `/v1/workspaces` | GET | `platform_routes.py` |
| `/v1/workspaces` | POST | `platform_routes.py` |
| `/v1/workspace/bootstrap` | POST | `platform_routes.py` |
| `/v1/search` | GET | `platform_routes.py` |
| `/v1/files` | GET | `platform_routes.py` |
| `/v1/files` | POST | `platform_routes.py` |
| `/v1/files/{file_id}` | GET | `platform_routes.py` |
| `/v1/files/{file_id}` | PATCH | `platform_routes.py` |
| `/v1/files/{file_id}` | DELETE | `platform_routes.py` |
| `/v1/library` | GET | `platform_routes.py` |
| `/v1/library` | POST | `platform_routes.py` |
| `/v1/library/{item_id}` | DELETE | `platform_routes.py` |
| `/v1/prompts` | GET | `platform_routes.py` |
| `/v1/prompts` | POST | `platform_routes.py` |
| `/v1/prompts/{prompt_id}` | PATCH | `platform_routes.py` |
| `/v1/prompts/{prompt_id}` | DELETE | `platform_routes.py` |
| `/v1/tasks` | GET | `platform_routes.py` |
| `/v1/tasks` | POST | `platform_routes.py` |
| `/v1/tasks/{task_id}` | PATCH | `platform_routes.py` |
| `/v1/tasks/{task_id}` | DELETE | `platform_routes.py` |
| `/v1/notifications` | GET | `platform_routes.py` |
| `/v1/notifications/{notif_id}/read` | POST | `platform_routes.py` |
| `/v1/settings` | GET | `platform_routes.py` |
| `/v1/settings` | PATCH | `platform_routes.py` |
| `/v1/knowledge/sources` | GET | `platform_routes.py` |
| `/v1/knowledge/sources` | POST | `platform_routes.py` |
| `/v1/knowledge/sources/{source_id}` | DELETE | `platform_routes.py` |
| `/v1/explore` | GET | `platform_routes.py` |
| `/v1/explore/{item_id}/use` | POST | `platform_routes.py` |
| `/v1/memories` | GET | `platform_routes.py` |
| `/v1/memories` | POST | `platform_routes.py` |
| `/v1/memories/{memory_id}` | PATCH | `platform_routes.py` |
| `/v1/memories/{memory_id}` | DELETE | `platform_routes.py` |
| `/v1/models/catalog` | GET | `platform_routes.py` |
| `/v1/history` | GET | `platform_routes.py` |
| `/v1/profile/me` | GET | `platform_routes.py` |
| `/v1/tools` | GET | `platform_routes.py` |
| `/v1/tools/{tool_id}` | PATCH | `platform_routes.py` |
| `/v1/scheduled-tasks` | GET | `platform_routes.py` |
| `/v1/scheduled-tasks` | POST | `platform_routes.py` |
| `/v1/projects/{project_id}/members` | GET | `platform_routes.py` |
| `/v1/projects/{project_id}/members` | POST | `platform_routes.py` |
| `/v1/projects/{project_id}/members/{member_id}` | DELETE | `platform_routes.py` |
| `/v1/instructions/versions` | GET | `platform_routes.py` |
| `/v1/instructions/versions` | POST | `platform_routes.py` |
| `/v1/library/{item_id}/favorite` | PATCH | `platform_routes.py` |
| `/v1/billing` | GET | `platform_routes.py` |
| `/v1/projects` | GET | `workspace_routes.py` |
| `/api/projects` | GET | `workspace_routes.py` |
| `/v1/projects/{project_id}` | GET | `workspace_routes.py` |
| `/api/projects/{project_id}` | GET | `workspace_routes.py` |
| `/v1/projects` | POST | `workspace_routes.py` |
| `/api/projects` | POST | `workspace_routes.py` |
| `/v1/projects/{project_id}` | PATCH | `workspace_routes.py` |
| `/v1/projects/{project_id}` | PUT | `workspace_routes.py` |
| `/api/projects/{project_id}` | PATCH | `workspace_routes.py` |
| `/api/projects/{project_id}` | PUT | `workspace_routes.py` |
| `/v1/projects/{project_id}` | DELETE | `workspace_routes.py` |
| `/api/projects/{project_id}` | DELETE | `workspace_routes.py` |
| `/v1/projects/{project_id}/duplicate` | POST | `workspace_routes.py` |
| `/api/projects/{project_id}/duplicate` | POST | `workspace_routes.py` |
| `/v1/projects/{project_id}/chats` | GET | `workspace_routes.py` |
| `/api/projects/{project_id}/chats` | GET | `workspace_routes.py` |
| `/v1/projects/{project_id}/chats` | POST | `workspace_routes.py` |
| `/api/projects/{project_id}/chats` | POST | `workspace_routes.py` |
| `/v1/projects/{project_id}/files` | GET | `workspace_routes.py` |
| `/api/projects/{project_id}/files` | GET | `workspace_routes.py` |
| `/v1/projects/{project_id}/files` | POST | `workspace_routes.py` |
| `/api/projects/{project_id}/files` | POST | `workspace_routes.py` |
| `/v1/projects/{project_id}/files/{file_id}` | DELETE | `workspace_routes.py` |
| `/api/projects/{project_id}/files/{file_id}` | DELETE | `workspace_routes.py` |
| `/v1/projects/{project_id}/memory` | GET | `workspace_routes.py` |
| `/api/projects/{project_id}/memory` | GET | `workspace_routes.py` |
| `/v1/projects/{project_id}/memory` | POST | `workspace_routes.py` |
| `/api/projects/{project_id}/memory` | POST | `workspace_routes.py` |
| `/v1/projects/{project_id}/memory/{memory_id}` | DELETE | `workspace_routes.py` |
| `/api/projects/{project_id}/memory/{memory_id}` | DELETE | `workspace_routes.py` |
| `/v1/projects/{project_id}/knowledge` | GET | `workspace_routes.py` |
| `/api/projects/{project_id}/knowledge` | GET | `workspace_routes.py` |
| `/v1/projects/{project_id}/knowledge` | POST | `workspace_routes.py` |
| `/api/projects/{project_id}/knowledge` | POST | `workspace_routes.py` |
| `/v1/assistants` | GET | `workspace_routes.py` |
| `/v1/assistants` | POST | `workspace_routes.py` |
| `/v1/assistants/{assistant_id}` | DELETE | `workspace_routes.py` |
| `/v1/assistants/{assistant_id}` | PATCH | `workspace_routes.py` |
| `/v1/assistants/{assistant_id}/duplicate` | POST | `workspace_routes.py` |
| `/v1/system-prompts` | GET | `workspace_routes.py` |
| `/v1/system-prompts` | POST | `workspace_routes.py` |
| `/v1/system-prompts/{name}` | DELETE | `workspace_routes.py` |

---

## 8. UI surfaces

| URL | File | Purpose |
|-----|------|---------|
| `/chat` | `om_ai/api/static/chat.html` | Main workspace (conversations, models, projects, multimodal) |
| `/login` | `om_ai/api/static/login.html` | Account login |
| `/register` | `om_ai/api/static/register.html` | Account register |
| `/tokens` | `om_ai/api/static/tokens.html` | API key management |
| `/static/icons/*` | `om_ai/api/static/icons/` | Favicons / brand |
| `/static/site.webmanifest` | PWA manifest |

Store backends for UI state:

- `om_ai/api/platform_store.py` — settings, library, prompts, tools, memories, catalog
- `om_ai/api/workspace_store.py` — projects, assistants, files, project memory
- `om_ai/api/conversations.py` + `om_ai/memory/conversations.py` — chats
- SQLite files under `artifacts/` (see §10)

---

## 9. CLI commands

Entry: `om_ai/cli.py` → console script `om-ai`.

| Command | Purpose |
|---------|---------|
| `om-ai serve` | Start FastAPI (`om_ai/api/main.py`) |
| `om-ai model-info` | Native model / registry info |
| `om-ai train-om1` | OM-1.0 local train loop |
| `om-ai train` / `pretrain` | Causal pretraining |
| `om-ai tokenizer train\|inspect\|encode\|decode` | Byte-BPE |
| `om-ai corpus …` | OMAI-Corpus-v1 governance |
| `om-ai sft` / `reward` / `dpo` | Post-training |
| `om-ai evaluate` / `benchmark` | Eval harness |
| `om-ai generate` / `chat` | Inference |
| `om-ai feedback add\|export` | Continuous learning I/O |
| `om-ai registry list\|register` | Model lifecycle |
| `om-ai bundle` | Checkpoint integrity bundle |
| `om-ai project-scan` | Local project discovery |
| `om-ai train-70b` | 70B cluster launcher |

Distillation helper (module):

```bash
python -m om_ai.tools.llm_harvest --task "..." --teachers openrouter --out data/om_distillation/
```

---

## 10. Configs, env, artifacts, data paths

### 10.1 Configs (`configs/`)

| File | Role |
|------|------|
| `tiny.json`, `om-tiny.json`, `omai-20m.json` | Tiny / smoke shapes |
| `om-1.0-local.json`, `om-1.0.json` | OM-1.0 local/prod shapes |
| `1b.json` … `70b.json`, `om-1b.json` … `om-70b.json` | Scale presets (shapes, not weights) |
| `deepspeed_zero3.json` | DeepSpeed ZeRO-3 |
| `train_70b_gates.json` | 70B gate checks |

### 10.2 Important env (see `.env.example`)

| Variable | Default / role |
|----------|----------------|
| `OM_MODEL_PROVIDER` | `om_native` |
| `OM_AI_CHAT_BACKEND` | `om_native` |
| `OM_MODEL_CHECKPOINT` | path to `.pt` |
| `OM_MODEL_TOKENIZER` | tokenizer JSON |
| `OM_MODEL_CONFIG` | architecture JSON |
| `OM_AI_DB` | `artifacts/om_ai.sqlite3` |
| `OM_AI_KB` | `artifacts/knowledge.sqlite3` |
| `OM_AI_TOKENS_DB` | `artifacts/tokens.sqlite3` |
| `OM_AI_ACCOUNTS_DB` | `artifacts/accounts.sqlite3` |
| `OM_AI_AUDIT_DB` | `artifacts/audit.sqlite3` |
| `OM_AI_FEEDBACK_DB` | `artifacts/feedback.sqlite3` |
| `OM_AI_REGISTRY` | `artifacts/registry` |
| `OM_AI_RATE_LIMIT` | req/min (0 = off) |
| `OM_AI_REQUIRE_AUTH` | force auth |
| `OPENROUTER_API_KEY` | OpenRouter teacher/chat |
| `OPENROUTER_MODEL` | override OpenRouter model id |

### 10.3 Artifacts (`artifacts/`)

Runtime / train outputs (often gitignored or large):

| Path | Role |
|------|------|
| `artifacts/checkpoints/` | Train checkpoints (`*/latest.pt`) |
| `artifacts/models/om-1.0/` | Registry metadata for OM-1.0 |
| `artifacts/registry/` | Model registry root |
| `artifacts/*.sqlite3` | App DBs (+ `-wal`/`-shm`) |
| `artifacts/uploads/` | User uploads |
| `artifacts/eval/` | Eval reports |
| `artifacts/tokenizer*.json` | Trained tokenizers |
| `artifacts/improvement/` | Improvement job outputs |
| `artifacts/demo/` | Tiny pipeline proof |

### 10.4 Data (`data/`)

| Path | Role |
|------|------|
| `data/omai-corpus-v1/` | Governed corpus build tree |
| `data/omai-genesis-v1/` | Genesis train/eval/raw |
| `data/om-knowledge-brain-v1/` | Era + domain knowledge brain |
| `data/om-knowledge-corpus/` | Knowledge corpus packs |
| `data/production-corpus/` | Production pretrain text |
| `data/om_distillation/` | Teacher harvest exports |
| `data/sft/`, `data/dpo/` | Alignment datasets |
| `data/om-memory/`, `data/om-goals/` | Memory/goals JSON |
| `data/om-code/` | Code index |
| `data/om-training/`, `data/om_training/` | Training staging |
| `data/continuous/` | Continuous learning buffers |

---

## 11. Services & infrastructure

### 11.1 `services/` packages

| Package | Role |
|---------|------|
| `api_gateway` | Gateway façade |
| `model_service` | Model serve stubs |
| `memory_service` | Memory service |
| `knowledge_service` | Knowledge service |
| `retrieval_service` | Retrieval |
| `reasoning_service` | Reasoning |
| `agent_service` | Agents |
| `evaluation_service` | Eval |
| `learning_service` | Learning |
| `identity_service` | Identity |
| `user_service` | Users |
| `audit_service` | Audit |
| `billing_service` | Billing stubs |
| `model_lifecycle` | Lifecycle |

Primary **monolith serve path** remains `om_ai/api/main.py`; services are modular packaging for future split deploy.

### 11.2 Infrastructure

- `infrastructure/docker/` — container assets  
- `infrastructure/kubernetes/` — k8s manifests  
- `infrastructure/terraform/` — IaC  
- `infrastructure/monitoring/` — monitoring stubs  
- Root `Dockerfile`, `docker-compose.yml`

---

## 12. Security & auth model

| File | Role |
|------|------|
| `om_ai/security/auth.py` | TenantContext, API key roles |
| `om_ai/security/accounts.py` | Email/password accounts |
| `om_ai/security/session_cookie.py` | Session cookies |
| `om_ai/security/tokens.py` | DB-backed API tokens |
| `om_ai/security/rate_limit.py` | Rate limiter |
| `om_ai/security/ssrf.py` | SSRF guard for URL tools |
| `om_ai/security/audit.py` / `audit_log.py` | Audit trail |
| `om_ai/security/sandbox.py` | Execution sandbox |
| `om_ai/security/policy.py` / `permission.py` | RBAC helpers |
| `om_ai/api/deps.py` | `require_auth`, `require_permission` |

Roles: `admin` | `operator` | `agent` | `viewer` (via `OM_AI_API_KEYS`).

---

## 13. Core functionality by domain

| Domain | Primary paths | What it does |
|--------|---------------|--------------|
| Model arch | `om_ai/model/` | RoPE, GQA/MHA, SwiGLU, KV cache Transformer |
| Train | `om_ai/training/` | Pretrain, SFT, DPO, PPO, 70B, DeepSpeed |
| Distill | `om_ai/core/distillation/` | Multi-teacher harvest → JSONL |
| Chat runtime | `om_ai/runtime/` | Backend selection, orchestrator, external LLMs |
| API/UI | `om_ai/api/` | FastAPI + static workspace |
| Memory | `om_ai/memory/` | SQLite multi-kind + conversations |
| Knowledge/RAG | `om_ai/knowledge/` | Ingest, chunk, vector/lexical retrieve, graph RAG |
| Live web | `om_ai/live_knowledge/` | Fetch/search (not a third-party chat LLM) |
| Agents | `om_ai/agents/`, `om_ai/actions/`, `om_ai/tools/` | Plan/tool/verify |
| Understanding | `om_ai/understanding/`, `om_ai/core/understanding/` | Intent, typo, freshness, context |
| Reasoning | `om_ai/core/reasoning/`, `om_ai/reasoning/` | Chains, planners, solvers |
| Response | `om_ai/core/response/`, `om_ai/response_engine/` | Format, stream, tools filter |
| Multimodal | `om_ai/multimodal/`, `om_ai/perception/`, `om_ai/vision/`, `om_ai/voice/` | Image/PDF/OCR/audio |
| OI / robotics | `om_ai/operating_intelligence/`, `om_ai/robotics/`, `om_ai/universal_robotics/` | Observe→Improve + embodiment |
| Safety | `om_ai/safety/`, `om_ai/security/` | Policy + platform security |
| Self-improve | `om_ai/self_improvement/`, `om_ai/improvement/`, `om_ai/continuous/` | Feedback → train queues |
| Knowledge brain | `om_ai/knowledge_brain/`, `data/om-knowledge-brain-v1/` | Era/domain knowledge packs |
| Data engine | `om_ai/data_engine/`, `om_ai/corpus/` | Connectors, curriculum, governance |

---

## 14. Complete `om_ai/` package & file inventory

Each row is a real file path under the repo. **Role** is taken from the module docstring when present, otherwise inferred from the filename.

### `om_ai/action/` — Built-in tool actions and execution helpers

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/action/__init__.py` |   init   |
| `om_ai/action/builtin_tools.py` | OM Built-in Autonomous Tools |
| `om_ai/action/executor.py` | OM Autonomous Tool Executor |
| `om_ai/action/planner.py` | OM Tool Selection Planner |
| `om_ai/action/registry.py` | OM Tool Registry Stores available tools. |
| `om_ai/action/tool.py` | OM Autonomous Tool Model |
| `om_ai/action/validator.py` | OM Tool Result Validator |

### `om_ai/actions/` — Safe shell / knowledge tools for agents

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/actions/__init__.py` |   init   |
| `om_ai/actions/base.py` | Tool base classes and result types. Every tool must: - Set class-level (or instance-level) name and description attribut |
| `om_ai/actions/knowledge.py` | knowledge |
| `om_ai/actions/shell.py` | SafeShellTool: deny-by-default subprocess execution with strict security controls. Security model: - argv[0] must be in  |

### `om_ai/agent/` — Coding agent and useful-reply helpers

**10 Python files**

| Path | Role |
|------|------|
| `om_ai/agent/__init__.py` | OM Agent Brain v1 — ChatGPT-style assistant layer on top of OM-1.0. This is the system layer (intent → memory/RAG/tools  |
| `om_ai/agent/brain.py` | AgentBrain — single entry for chat: understand → intent → gather → hint/fallback. |
| `om_ai/agent/coding_agent.py` | OM Coding Agent — repository-aware plan / analyze loop. Capabilities (software): - Read repository map - Understand roug |
| `om_ai/agent/context.py` | Tiny-context conversation packing for OM-1.0 (max_seq_len often 128). |
| `om_ai/agent/executor.py` | Execute Agent Brain plans: gather evidence AND run planned tools. |
| `om_ai/agent/intent.py` | Intent classification for OM Agent Brain (no external LLM). |
| `om_ai/agent/planner.py` | Lightweight planner for chat Agent Brain (wraps RulePlanner). |
| `om_ai/agent/tools.py` | Chat-safe tools for Agent Brain (knowledge + live freshness hints). |
| `om_ai/agent/useful_reply.py` | Useful assistant replies when the tiny model fails (not static bridge text). |
| `om_ai/agent/verifier.py` | Verifier for Agent Brain replies. |

### `om_ai/agents/` — Multi-agent orchestrator, roles, allocation, collaboration

**23 Python files**

| Path | Role |
|------|------|
| `om_ai/agents/__init__.py` |   init   |
| `om_ai/agents/allocation/__init__.py` |   init   |
| `om_ai/agents/allocation/allocator.py` | OM Dynamic Agent Allocation Engine |
| `om_ai/agents/allocation/capability.py` | OM Agent Capability Model |
| `om_ai/agents/allocation/memory.py` | OM Agent Performance Memory |
| `om_ai/agents/allocation/registry.py` | OM Agent Capability Registry |
| `om_ai/agents/allocation/scorer.py` | OM Agent Selection Scoring |
| `om_ai/agents/base.py` | OM Agent Base Class |
| `om_ai/agents/business_agent.py` | OM Business Agent Handles: - Business logic - Finance - Operations |
| `om_ai/agents/coding_agent.py` | OM Coding Agent Handles: - Programming - Debugging - Architecture - Implementation |
| `om_ai/agents/collaboration/__init__.py` |   init   |
| `om_ai/agents/collaboration/coordinator.py` | OM Multi Agent Coordinator Executes multiple agents together. |
| `om_ai/agents/collaboration/planner.py` | OM Multi Agent Planner Decides which agents should work together. |
| `om_ai/agents/database_agent.py` | OM Database Agent Handles: - Database design - Schema planning - Migration - Data modeling |
| `om_ai/agents/executor.py` | OM Agent Execution Engine Runs selected agent behavior. Flow: Agent Router / ↓ Agent Executor / ├── Tool Router / ├── To |
| `om_ai/agents/general_agent.py` | general agent |
| `om_ai/agents/memory_agent.py` | OM Memory Agent Handles: - User memory - Project memory - Context recall |
| `om_ai/agents/orchestrator.py` | AgentOrchestrator: multi-step goal execution engine. Features: - Pluggable LLM engine (object with .generate(prompt, **k |
| `om_ai/agents/research_agent.py` | Research Agent |
| `om_ai/agents/roles.py` | OM Agent role registry — Master + specialist agents (thin definitions). |
| `om_ai/agents/router.py` | OM Agent Router Selects best agent. |
| `om_ai/agents/runtime.py` | Agent Runtime — workers that can plan and (gated) act on a repository. |
| `om_ai/agents/specialists.py` | Specialist agents — produce real work products (plans, reviews, schemas), not labels. |

### `om_ai/api/` — FastAPI app, routers, static UI, platform/workspace stores

**13 Python files**

| Path | Role |
|------|------|
| `om_ai/api/__init__.py` |   init   |
| `om_ai/api/auth_routes.py` | Account register / login / logout / me API (cookie + Bearer). |
| `om_ai/api/conversations.py` | conversations |
| `om_ai/api/deps.py` | FastAPI auth dependencies (requires fastapi). |
| `om_ai/api/foundation_routes.py` | Foundation APIs: knowledge, reasoning, evaluation, learning. |
| `om_ai/api/main.py` | main |
| `om_ai/api/oi_routes.py` | Operating Intelligence API — capability board + Observe→Improve cycle. |
| `om_ai/api/onboarding.py` | onboarding |
| `om_ai/api/openai_compat.py` | openai compat |
| `om_ai/api/platform_routes.py` | platform routes |
| `om_ai/api/platform_store.py` | Production platform store: workspaces, files, library, prompts, tasks, settings, knowledge sources. |
| `om_ai/api/workspace_routes.py` | workspace routes |
| `om_ai/api/workspace_store.py` | workspace store |

### `om_ai/autonomous/` — Autonomous planner loop

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/autonomous/__init__.py` |   init   |
| `om_ai/autonomous/dependency.py` | OM Task Dependency Graph |
| `om_ai/autonomous/executor.py` | OM Autonomous Task Executor |
| `om_ai/autonomous/planner.py` | OM Autonomous Task Planner |
| `om_ai/autonomous/task.py` | OM Autonomous Task Model |
| `om_ai/autonomous/tracker.py` | OM Task Progress Tracker |
| `om_ai/autonomous/validator.py` | OM Autonomous Result Validator |

### `om_ai/autonomy/` — Task queue, executor, evaluation loops

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/autonomy/__init__.py` |   init   |
| `om_ai/autonomy/evaluation/__init__.py` |   init   |
| `om_ai/autonomy/evaluation/correction.py` | OM Correction Planner Creates improvement actions. |
| `om_ai/autonomy/evaluation/loop.py` | OM Self Correction Loop |
| `om_ai/autonomy/evaluation/quality_checker.py` | OM Quality Checker Evaluates generated results. |
| `om_ai/autonomy/executor.py` | OM Autonomous Executor |
| `om_ai/autonomy/goal.py` | OM Goal Model Represents user objectives. |
| `om_ai/autonomy/planner.py` | OM Autonomous Planner Breaks goals into executable tasks. |
| `om_ai/autonomy/task_queue.py` | OM Task Queue Stores execution tasks. |

### `om_ai/backends/` — OM native / OpenAI-compatible / stub backends

**6 Python files**

| Path | Role |
|------|------|
| `om_ai/backends/__init__.py` |   init   |
| `om_ai/backends/base.py` | base |
| `om_ai/backends/checkpoint_checker.py` | OM-1.0 checkpoint verification — non-fatal for serve bootstrap. |
| `om_ai/backends/om_native.py` | om native |
| `om_ai/backends/om_registry.py` | OM-1.0 model registry under ``artifacts/models/om-1.0/`` (truthful metadata only). |
| `om_ai/backends/stubs.py` | Protocol aliases for OM backends — point at real modules (not unfinished work). Historically this file held PHASE 11–15  |

### `om_ai/brain/` — High-level brain facade

**2 Python files**

| Path | Role |
|------|------|
| `om_ai/brain/__init__.py` | OM Brain package — dataset-powered cognition over local corpora. |
| `om_ai/brain/dataset_engine.py` | dataset engine |

### `om_ai/checkpoint/` — Checkpoint bundle + integrity

**2 Python files**

| Path | Role |
|------|------|
| `om_ai/checkpoint/__init__.py` | OM AI checkpoint bundle package. Exports ------- CheckpointBundle – dataclass holding all bundle metadata and loaded sta |
| `om_ai/checkpoint/bundle.py` | Checkpoint bundle management for OM AI model artefacts. Bundle layout:: <root>/models/OM-LM-<name>/ config.json tokenize |

### `om_ai/cli_commands/` — Extra CLI command modules

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/cli_commands/__init__.py` | OM AI CLI Commands Package Contains command groups: - Distillation commands (Typer group under distill routing) - Learni |
| `om_ai/cli_commands/distill_commands.py` | distill commands |
| `om_ai/cli_commands/distill_config.py` | distill config |
| `om_ai/cli_commands/learn_commands.py` | argparse handlers for ``om-ai learn`` (not Typer — matches main CLI). Background learning loop: Gaps → Scheduler → Teach |

### `om_ai/code_intelligence/` — Repo scanning / code understanding

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/code_intelligence/__init__.py` |   init   |
| `om_ai/code_intelligence/architecture.py` | OM Architecture Understanding Engine |
| `om_ai/code_intelligence/dependency.py` | OM Dependency Intelligence |
| `om_ai/code_intelligence/engine.py` | OM Repository Intelligence Engine |
| `om_ai/code_intelligence/file_analyzer.py` | OM File Intelligence Analyzer |
| `om_ai/code_intelligence/index.py` | OM Repository Knowledge Index |
| `om_ai/code_intelligence/language.py` | OM Programming Language Detector |
| `om_ai/code_intelligence/scanner.py` | OM Repository Scanner Finds files inside a project. |

### `om_ai/coding_brain/` — Coding-focused reasoning helpers

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/coding_brain/__init__.py` | Coding brain — language/framework skills + coding agent facade. |

### `om_ai/cognition/` — Cognition layer stubs

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/cognition/__init__.py` | Cognition runtime — intent → reason → retrieve → verify (production path). |
| `om_ai/cognition/intent_engine.py` | OM AI Intent Understanding Engine Purpose: - Understand user intention before RAG retrieval - Detect domain - Detect tas |
| `om_ai/cognition/task_planner.py` | OM-1.0 Task Decomposition Engine Purpose: Break user requirements into smaller executable tasks. Input: User request Out |
| `om_ai/cognition/technology_engine.py` | OM-1.0 Technology Understanding Engine. Structured stack detection only — not answer generation. Longest phrase wins so  |

### `om_ai/cognitive/` — Cognitive pipeline pieces

**3 Python files**

| Path | Role |
|------|------|
| `om_ai/cognitive/__init__.py` | OM Human-Like Cognitive Pipeline — understand meaning before answering. Flow: User input → spelling → language → intent  |
| `om_ai/cognitive/explanation.py` | Explanation intelligence — adjust depth and tone to the user. |
| `om_ai/cognitive/goal_detector.py` | User goal detection with conversation context. |

### `om_ai/collaboration/` — Agent collaboration bus / coordinator

**6 Python files**

| Path | Role |
|------|------|
| `om_ai/collaboration/__init__.py` |   init   |
| `om_ai/collaboration/bus.py` | OM Agent Communication Bus Handles agent-to-agent messages. |
| `om_ai/collaboration/coordinator.py` | OM Multi Agent Coordinator |
| `om_ai/collaboration/memory.py` | OM Agent Shared Memory |
| `om_ai/collaboration/message.py` | OM Agent Communication Message |
| `om_ai/collaboration/workspace.py` | OM Shared Agent Workspace |

### `om_ai/context/` — Context assembly helpers

**6 Python files**

| Path | Role |
|------|------|
| `om_ai/context/__init__.py` |   init   |
| `om_ai/context/analyzer.py` | OM Context Analyzer |
| `om_ai/context/context.py` | OM Context Model |
| `om_ai/context/engine.py` | OM Autonomous Context Awareness Engine |
| `om_ai/context/environment.py` | OM Environment Awareness |
| `om_ai/context/situation.py` | OM Situation Understanding |

### `om_ai/continuous/` — Feedback store + continuous learning export

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/continuous/__init__.py` |   init   |
| `om_ai/continuous/cycle.py` | Continuous learning cycle: feedback → datasets → fine-tune recipe. |
| `om_ai/continuous/feedback.py` | feedback |
| `om_ai/continuous/replay.py` | replay |

### `om_ai/conversation_engine/` — Conversation management engine

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/conversation_engine/__init__.py` | OM Human-like Conversation Engine — understand before answering. |

### `om_ai/core/` — Core cognitive, distillation, learning, reasoning, steps

**230 Python files**

| Path | Role |
|------|------|
| `om_ai/core/__init__.py` | OM AI Foundation — core intelligence modules (additive, non-breaking). |
| `om_ai/core/advanced_learning/__init__.py` |   init   |
| `om_ai/core/advanced_learning/advanced_learning_engine.py` | advanced learning engine |
| `om_ai/core/advanced_learning/dataset_generator.py` | dataset generator |
| `om_ai/core/advanced_learning/evaluation_engine.py` | evaluation engine |
| `om_ai/core/advanced_learning/improvement_planner.py` | improvement planner |
| `om_ai/core/advanced_learning/knowledge_builder.py` | knowledge builder |
| `om_ai/core/advanced_learning/learning_record.py` | learning record |
| `om_ai/core/advanced_learning/pattern_learner.py` | pattern learner |
| `om_ai/core/agents/__init__.py` | OM AI Autonomous Agent Civilization Layer Provides: - Agent foundation - Agent registry - Agent manager - Agent communic |
| `om_ai/core/agents/agent.py` | agent |
| `om_ai/core/agents/agent_communication.py` | agent communication |
| `om_ai/core/agents/agent_evaluator.py` | agent evaluator |
| `om_ai/core/agents/agent_manager.py` | agent manager |
| `om_ai/core/agents/agent_memory.py` | agent memory |
| `om_ai/core/agents/agent_registry.py` | agent registry |
| `om_ai/core/agents/agent_router.py` | agent router |
| `om_ai/core/agents/agent_state.py` | agent state |
| `om_ai/core/agents/base_agent.py` | base agent |
| `om_ai/core/agents/coding_agent.py` | coding agent |
| `om_ai/core/agents/collaboration_engine.py` | collaboration engine |
| `om_ai/core/agents/knowledge_agent.py` | knowledge agent |
| `om_ai/core/agents/memory_agent.py` | memory agent |
| `om_ai/core/agents/quality_agent.py` | quality agent |
| `om_ai/core/agents/research_agent.py` | research agent |
| `om_ai/core/agents/security_agent.py` | security agent |
| `om_ai/core/agents/team_builder.py` | team builder |
| `om_ai/core/civilization/__init__.py` |   init   |
| `om_ai/core/civilization/agent_communication.py` | agent communication |
| `om_ai/core/civilization/agent_evaluator.py` | agent evaluator |
| `om_ai/core/civilization/agent_manager.py` | agent manager |
| `om_ai/core/civilization/agent_profile.py` | agent profile |
| `om_ai/core/civilization/civilization_engine.py` | civilization engine |
| `om_ai/core/civilization/mission.py` | mission |
| `om_ai/core/civilization/mission_planner.py` | mission planner |
| `om_ai/core/civilization/task_delegator.py` | task delegator |
| `om_ai/core/coding/architecture_planner.py` | architecture planner |
| `om_ai/core/coding/coding_intelligence.py` | coding intelligence |
| `om_ai/core/coding/coding_orchestrator.py` | coding orchestrator |
| `om_ai/core/coding/requirement_analyzer.py` | requirement analyzer |
| `om_ai/core/cognitive/__init__.py` | OM Cognitive Intelligence Layer. This package exposes the core cognitive systems used by OM: - Cognitive Engine - OM Cog |
| `om_ai/core/cognitive/agent_collaboration.py` | agent collaboration |
| `om_ai/core/cognitive/brain_pipeline.py` | brain pipeline |
| `om_ai/core/cognitive/cognitive_engine.py` | cognitive engine |
| `om_ai/core/cognitive/context_manager.py` | Context manager stub used by cognitive package exports. |
| `om_ai/core/cognitive/decision_engine.py` | Decision stub used by cognitive package exports. |
| `om_ai/core/cognitive/intelligence_state.py` | Intelligence state stub used by cognitive package exports. |
| `om_ai/core/cognitive/planner.py` | planner |
| `om_ai/core/cognitive/reasoning_engine.py` | reasoning engine |
| `om_ai/core/cognitive/response_engine.py` | response engine |
| `om_ai/core/cognitive/self_evaluator.py` | self evaluator |
| `om_ai/core/config.py` | config |
| `om_ai/core/context/__init__.py` | Context helpers for OM brain. |
| `om_ai/core/context/context_intelligence.py` | Rank and compress retrieved context for the model prompt. |
| `om_ai/core/distillation/__init__.py` | OM Multi-LLM Teacher Distillation — STEP 94. Harvest answers from connected external LLMs (GPT/Claude/Gemini/Qwen/…), cl |
| `om_ai/core/distillation/agreement_engine.py` | agreement engine |
| `om_ai/core/distillation/answer_comparator.py` | Compare teacher answers and extract shared / unique points. |
| `om_ai/core/distillation/answer_synthesizer.py` | answer synthesizer |
| `om_ai/core/distillation/checkpoint_manager.py` | checkpoint manager |
| `om_ai/core/distillation/config.py` | config |
| `om_ai/core/distillation/continuous_loop.py` | STEP 94.14 — Continuous Distillation Loop. Gaps → Curriculum → Schedule → Harvest/Distill → Teacher Intelligence update. |
| `om_ai/core/distillation/contradiction_detector.py` | contradiction detector |
| `om_ai/core/distillation/curriculum_generator.py` | STEP 94.11 — Curriculum Generator. Build progressive question curricula for teacher distillation by domain and level. |
| `om_ai/core/distillation/dataset_builder.py` | Build OM training records from ranked teacher knowledge. |
| `om_ai/core/distillation/distillation_engine.py` | distillation engine |
| `om_ai/core/distillation/distillation_state.py` | Persistent paths and run state for teacher distillation. |
| `om_ai/core/distillation/evaluation_builder.py` | evaluation builder |
| `om_ai/core/distillation/factory.py` | Factory helpers for OM distillation engine + STEP 94.10–94.14 stack. |
| `om_ai/core/distillation/harvest_engine.py` | harvest engine |
| `om_ai/core/distillation/harvest_scheduler.py` | STEP 94.12 — Autonomous Harvest Scheduler. Queue and run distillation harvest jobs without blocking chat. |
| `om_ai/core/distillation/knowledge_collector.py` | Clean → verify → store knowledge (never training on raw dumps alone). |
| `om_ai/core/distillation/knowledge_distiller.py` | knowledge distiller |
| `om_ai/core/distillation/knowledge_extractor.py` | knowledge extractor |
| `om_ai/core/distillation/knowledge_gap_collector.py` | STEP 94.13 — Knowledge Gap Collector. Find weak/missing topics from chat quality, failed distillations, and explicit mar |
| `om_ai/core/distillation/knowledge_writer.py` | knowledge writer |
| `om_ai/core/distillation/llm_harvester.py` | llm harvester |
| `om_ai/core/distillation/models.py` | models |
| `om_ai/core/distillation/ollama_client.py` | Local Ollama HTTP client for teacher distillation. |
| `om_ai/core/distillation/preference_builder.py` | preference builder |
| `om_ai/core/distillation/progress_tracker.py` | progress tracker |
| `om_ai/core/distillation/provenance_manager.py` | provenance manager |
| `om_ai/core/distillation/quality_evaluator.py` | quality evaluator |
| `om_ai/core/distillation/quality_ranker.py` | Rank teacher answers by structure, coverage, and safety signals. |
| `om_ai/core/distillation/response_normalizer.py` | response normalizer |
| `om_ai/core/distillation/sft_builder.py` | sft builder |
| `om_ai/core/distillation/startup.py` | startup |
| `om_ai/core/distillation/teacher_intelligence.py` | STEP 94.10 — Teacher Intelligence. Track which teachers win on which domains, recommend routing, and score reliability.  |
| `om_ai/core/distillation/teacher_manager.py` | TeacherManager — orchestrate Multi-LLM harvest → train export. |
| `om_ai/core/distillation/teacher_registry.py` | teacher registry |
| `om_ai/core/distillation/training_exporter.py` | Export distillation datasets to JSONL for OM SFT/DPO. |
| `om_ai/core/intelligence/__init__.py` | OM Core Cognitive Intelligence — understand before answering. |
| `om_ai/core/intelligence/capability_router.py` | Route intent → capability. Real answers only — never canned outlines. |
| `om_ai/core/intelligence/context_manager.py` | Load conversation / project / preference context before answering. |
| `om_ai/core/intelligence/freshness_detector.py` | Freshness detection — decide when live research is needed. |
| `om_ai/core/intelligence/intent_engine.py` | Normalize understanding into canonical intents. |
| `om_ai/core/intelligence/manager.py` | Cognitive intelligence manager. User → Understand → Think → Retrieve → Plan → Generate → Verify → Reply |
| `om_ai/core/intelligence/real_answer.py` | real answer |
| `om_ai/core/intelligence/response_validator.py` | Validate that the answer matches understanding — reject echoes and wrong intents. |
| `om_ai/core/intelligence/self_correction.py` | Regenerate when validation fails — capability re-run or clarification. |
| `om_ai/core/intelligence/tool_planner.py` | Decide which tools are needed — delegates to STEP 86 ToolDecisionEngine. |
| `om_ai/core/intelligence/understanding_engine.py` | Structured meaning from raw text — schema affinity, not keyword if/else. |
| `om_ai/core/intent_engine/__init__.py` | OM intent engine package. |
| `om_ai/core/intent_engine/classifier.py` | Intent engine — classify / route / detect task (wraps understanding + analyzer). |
| `om_ai/core/intent_engine/router.py` | Route classified intents to agents / pipelines. |
| `om_ai/core/intent_engine/task_detector.py` | Task detector — thin alias over classifier.detect_task. |
| `om_ai/core/knowledge_fusion/__init__.py` |   init   |
| `om_ai/core/knowledge_fusion/context_ranker.py` | context ranker |
| `om_ai/core/knowledge_fusion/fusion_engine.py` | fusion engine |
| `om_ai/core/knowledge_fusion/knowledge_selector.py` | knowledge selector |
| `om_ai/core/knowledge_fusion/retriever.py` | retriever |
| `om_ai/core/knowledge_intelligence/__init__.py` |   init   |
| `om_ai/core/knowledge_intelligence/knowledge_graph.py` | knowledge graph |
| `om_ai/core/knowledge_intelligence/knowledge_item.py` | knowledge item |
| `om_ai/core/knowledge_intelligence/knowledge_state.py` | knowledge state |
| `om_ai/core/knowledge_intelligence/knowledge_store.py` | knowledge store |
| `om_ai/core/knowledge_intelligence/rag_engine.py` | rag engine |
| `om_ai/core/knowledge_intelligence/research_engine.py` | research engine |
| `om_ai/core/knowledge_intelligence/research_planner.py` | research planner |
| `om_ai/core/knowledge_intelligence/source_evaluator.py` | source evaluator |
| `om_ai/core/learning/__init__.py` |   init   |
| `om_ai/core/learning/behavior_optimizer.py` | behavior optimizer |
| `om_ai/core/learning/distillation_worker.py` | Distillation worker — run teacher harvest jobs for the learning loop. |
| `om_ai/core/learning/evaluator.py` | evaluator |
| `om_ai/core/learning/experience.py` | experience |
| `om_ai/core/learning/experience_collector.py` | experience collector |
| `om_ai/core/learning/experience_memory.py` | experience memory |
| `om_ai/core/learning/failure_detector.py` | failure detector |
| `om_ai/core/learning/feedback_analyzer.py` | feedback analyzer |
| `om_ai/core/learning/improvement_analyzer.py` | improvement analyzer |
| `om_ai/core/learning/improvement_cycle.py` | Improvement cycle — orchestrate autonomous OM learning loop. |
| `om_ai/core/learning/improvement_engine.py` | improvement engine |
| `om_ai/core/learning/improvement_planner.py` | improvement planner |
| `om_ai/core/learning/knowledge_updater.py` | knowledge updater |
| `om_ai/core/learning/learning_analyzer.py` | learning analyzer |
| `om_ai/core/learning/learning_engine.py` | STEP 83 core LearningEngine — robust continuous learning loop. |
| `om_ai/core/learning/learning_manager.py` | learning manager |
| `om_ai/core/learning/learning_scheduler.py` | STEP 94.15 — Learning Scheduler. Pull knowledge gaps / curriculum topics into a runnable learning queue. |
| `om_ai/core/learning/learning_state.py` | STEP 83 core LearningState. |
| `om_ai/core/learning/skill_tracker.py` | skill tracker |
| `om_ai/core/learning/training_queue.py` | Training queue — stage distilled SFT/DPO examples for OM training. |
| `om_ai/core/memory/__init__.py` |   init   |
| `om_ai/core/memory/episodic_memory.py` | episodic memory |
| `om_ai/core/memory/experience_analyzer.py` | experience analyzer |
| `om_ai/core/memory/experience_memory.py` | experience memory |
| `om_ai/core/memory/long_term_memory.py` | long term memory |
| `om_ai/core/memory/memory_evaluator.py` | memory evaluator |
| `om_ai/core/memory/memory_item.py` | memory item |
| `om_ai/core/memory/memory_manager.py` | memory manager |
| `om_ai/core/memory/memory_retriever.py` | memory retriever |
| `om_ai/core/memory/memory_state.py` | memory state |
| `om_ai/core/memory/memory_store.py` | memory store |
| `om_ai/core/memory/semantic_memory.py` | semantic memory |
| `om_ai/core/memory/short_term_memory.py` | short term memory |
| `om_ai/core/reasoning/__init__.py` | OM-1.0 Cognition Layer — analyze, plan, solve, verify. |
| `om_ai/core/reasoning/analyzer.py` | Intent / understanding analyzer. |
| `om_ai/core/reasoning/chain_reasoner.py` | chain reasoner |
| `om_ai/core/reasoning/coding_intelligence.py` | OM Coding Intelligence Engine Purpose: Understand software requests and create dynamic coding plans. This module does NO |
| `om_ai/core/reasoning/critic.py` | critic |
| `om_ai/core/reasoning/pipeline.py` | pipeline |
| `om_ai/core/reasoning/planner.py` | Planning engine — ordered steps from intent. |
| `om_ai/core/reasoning/problem_analyzer.py` | problem analyzer |
| `om_ai/core/reasoning/reasoning_chain.py` | OM-1.0 Reasoning Chain Engine Purpose: Convert understanding into structured reasoning. This does not generate final ans |
| `om_ai/core/reasoning/reasoning_engine.py` | OM Reasoning Engine — deep chain with STEP 88 advanced reasoning. |
| `om_ai/core/reasoning/reasoning_state.py` | reasoning state |
| `om_ai/core/reasoning/reflection.py` | Self-reflection / critique for continuous improvement signals. |
| `om_ai/core/reasoning/solution_planner.py` | solution planner |
| `om_ai/core/reasoning/solver.py` | solver |
| `om_ai/core/reasoning/verifier.py` | Verification engine — internal checks before final answer. |
| `om_ai/core/research/__init__.py` |   init   |
| `om_ai/core/research/citation_manager.py` | citation manager |
| `om_ai/core/research/content_extractor.py` | content extractor |
| `om_ai/core/research/fact_verifier.py` | fact verifier |
| `om_ai/core/research/page_reader.py` | page reader |
| `om_ai/core/research/research_engine.py` | research engine |
| `om_ai/core/research/research_state.py` | research state |
| `om_ai/core/research/search_agent.py` | search agent |
| `om_ai/core/research/source_ranker.py` | source ranker |
| `om_ai/core/research/web_connector.py` | web connector |
| `om_ai/core/response/__init__.py` | Core response package. |
| `om_ai/core/response/answer_generator.py` | OM-1.0 Answer Generator Creates final human readable responses. Modes: user: Clean ChatGPT style answer developer: Full  |
| `om_ai/core/response/answer_planner.py` | answer planner |
| `om_ai/core/response/answer_verifier.py` | answer verifier |
| `om_ai/core/response/context_filter.py` | context filter |
| `om_ai/core/response/format_engine.py` | Response Formatting Engine — short vs structured vs table vs highlights. |
| `om_ai/core/response/format_selector.py` | format selector |
| `om_ai/core/response/formatter.py` | Response formatter — wraps response_engine. |
| `om_ai/core/response/garbage_detector.py` | Detect corrupted / meaningless model output and nonsense user asks. |
| `om_ai/core/response/improvement_engine.py` | improvement engine |
| `om_ai/core/response/intelligence.py` | Response Quality Engine — structure, grammar heuristics, solve-check, polish. |
| `om_ai/core/response/intent_classifier.py` | intent classifier |
| `om_ai/core/response/leakage_detector.py` | Dataset / training-leakage protection for public answers. |
| `om_ai/core/response/quality.py` | Response quality gate — wraps chat orchestrator checks. |
| `om_ai/core/response/quality_checker.py` | quality checker |
| `om_ai/core/response/response_engine.py` | response engine |
| `om_ai/core/response/response_formatter.py` | response formatter |
| `om_ai/core/response/response_intent.py` | response intent |
| `om_ai/core/response/response_memory.py` | response memory |
| `om_ai/core/response/response_state.py` | response state |
| `om_ai/core/response/response_strategy.py` | response strategy |
| `om_ai/core/response/self_critic.py` | Self-critic for OM answers — empty, topic, repeats, leakage, garbage. |
| `om_ai/core/response/tool_filter.py` | Strip / block tool-trace leakage from public answers. |
| `om_ai/core/steps/__init__.py` | OM STEPs 83–94 roadmap intelligence. |
| `om_ai/core/steps/stack.py` | OM Roadmap Stack — STEPs 83–94 unified runtime. |
| `om_ai/core/steps/step83_continuous_learning.py` | STEP 83 — Continuous Learning Intelligence. Flow: answer → was it good? → what failed? → store experience → improve next |
| `om_ai/core/steps/step84_advanced_learning.py` | STEP 84 — Advanced Learning Intelligence. Pattern mining → knowledge building → dataset generation → evaluation → improv |
| `om_ai/core/steps/step85_agent_civilization.py` | STEP 85 — Autonomous Agent Civilization. Mission planning → specialist agents → communication → evaluation. |
| `om_ai/core/steps/step86_global_knowledge.py` | STEP 86 — Global Knowledge Intelligence. Local knowledge + live retrieval + graph facts + ranking. |
| `om_ai/core/steps/step87_research.py` | STEP 87 marker — Research Intelligence (already implemented under core/research). |
| `om_ai/core/steps/step88_advanced_reasoning.py` | STEP 88 — Advanced Reasoning Intelligence. Requirements → hypotheses → alternatives → verification → final reasoning. |
| `om_ai/core/steps/step89_long_context.py` | STEP 89 — Long Context Intelligence. Conversation memory → summarization → importance ranking → recall. |
| `om_ai/core/steps/step90_agent_collaboration.py` | STEP 90 — Agent Collaboration Upgrade. Planner / Research / Coding / Testing / Security / Review / Deployment / Coordina |
| `om_ai/core/steps/step91_self_improvement.py` | STEP 91 — Self Improvement Engine. Previous answer → quality → failure analysis → improvement suggestions → behavior upd |
| `om_ai/core/steps/step92_knowledge_brain.py` | STEP 92 — Knowledge Brain. Document/web facts → graph → entity linking → verification → citations. |
| `om_ai/core/steps/step93_model_training.py` | STEP 93 — Model Training Intelligence (OM-native). Brain-facing training control plane for SFT / DPO / eval on local OM  |
| `om_ai/core/steps/step94_teacher_distillation.py` | STEP 94 — OM Multi-LLM Teacher Distillation Intelligence (+ 94.10–94.14). Harvest connected teacher LLM answers → clean/ |
| `om_ai/core/training_intelligence/__init__.py` |   init   |
| `om_ai/core/training_intelligence/config.py` | config |
| `om_ai/core/training_intelligence/knowledge_sampler.py` | knowledge sampler |
| `om_ai/core/training_intelligence/models.py` | models |
| `om_ai/core/understanding/__init__.py` |   init   |
| `om_ai/core/understanding/confidence_engine.py` | confidence engine |
| `om_ai/core/understanding/context_analyzer.py` | context analyzer |
| `om_ai/core/understanding/context_intent.py` | Context Intent Classifier — Tool Decision Layer front door. Replaces naive: if "date" in message → use_date_tool intent  |
| `om_ai/core/understanding/entity_extractor.py` | entity extractor |
| `om_ai/core/understanding/freshness_detector.py` | freshness detector |
| `om_ai/core/understanding/intent_engine.py` | intent engine |
| `om_ai/core/understanding/intent_state.py` | intent state |
| `om_ai/core/understanding/message_reader.py` | message reader |
| `om_ai/core/understanding/semantic_parser.py` | semantic parser |
| `om_ai/core/understanding/tool_decision_engine.py` | tool decision engine |

### `om_ai/corpus/` — Corpus catalog, filters, governance

**5 Python files**

| Path | Role |
|------|------|
| `om_ai/corpus/__init__.py` |   init   |
| `om_ai/corpus/filters.py` | Corpus document filters: language, quality, toxicity heuristics, PII. |
| `om_ai/corpus/omai_v1.py` | omai v1 |
| `om_ai/corpus/service.py` | service |
| `om_ai/corpus/sources_catalog.py` | Approved open training-data catalog for OM AI (license-first). These are *sources* you may legally collect into OMAI-Cor |

### `om_ai/data/` — Dataset helpers

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/data/__init__.py` |   init   |
| `om_ai/data/dataset.py` | dataset |
| `om_ai/data/governance.py` | governance |
| `om_ai/data/pipeline.py` | pipeline |

### `om_ai/data_engine/` — Ingestion connectors, curriculum, continuous data improvement

**40 Python files**

| Path | Role |
|------|------|
| `om_ai/data_engine/__init__.py` | OM Data Engine Responsible for: - Dataset ingestion - Cleaning - Quality filtering - Classification - Training dataset c |
| `om_ai/data_engine/benchmark/__init__.py` |   init   |
| `om_ai/data_engine/benchmark/benchmark.py` | OM Dataset Benchmark Engine |
| `om_ai/data_engine/benchmark/evaluator.py` | OM Dataset Evaluator |
| `om_ai/data_engine/benchmark/metrics.py` | OM Dataset Quality Metrics |
| `om_ai/data_engine/benchmark/report.py` | OM Benchmark Report Generator |
| `om_ai/data_engine/connectors/__init__.py` | OM Data Engine Connectors |
| `om_ai/data_engine/connectors/base.py` | OM Data Engine Base Dataset Connector All dataset connectors must follow this interface. |
| `om_ai/data_engine/connectors/github_code.py` | OM Data Engine Code Dataset Connector |
| `om_ai/data_engine/connectors/huggingface.py` | OM Data Engine HuggingFace Dataset Connector |
| `om_ai/data_engine/connectors/wikipedia.py` | OM Data Engine Wikipedia Connector |
| `om_ai/data_engine/continuous/__init__.py` |   init   |
| `om_ai/data_engine/continuous/deduplicator.py` | OM Dataset Deduplicator |
| `om_ai/data_engine/continuous/pipeline.py` | OM Continuous Learning Pipeline |
| `om_ai/data_engine/continuous/quality_filter.py` | OM Training Quality Filter |
| `om_ai/data_engine/continuous/validator.py` | OM Dataset Validator Checks training examples. |
| `om_ai/data_engine/continuous/version_manager.py` | OM Dataset Version Manager |
| `om_ai/data_engine/curriculum/__init__.py` |   init   |
| `om_ai/data_engine/curriculum/curriculum.py` | OM Dataset Curriculum Builder Creates learning progression. |
| `om_ai/data_engine/curriculum/levels.py` | OM Training Difficulty Levels |
| `om_ai/data_engine/curriculum/scheduler.py` | OM Training Scheduler Creates training order. |
| `om_ai/data_engine/curriculum/training_plan.py` | OM Training Plan Creates SFT/DPO roadmap. |
| `om_ai/data_engine/factory.py` | OM-1.0 Knowledge Factory Complete data generation pipeline. Sources: HuggingFace Wikipedia GitHub Code Flow: Source / ↓  |
| `om_ai/data_engine/improvement/__init__.py` |   init   |
| `om_ai/data_engine/improvement/detector.py` | OM Dataset Problem Detector Finds weak training samples. |
| `om_ai/data_engine/improvement/history.py` | OM Improvement History Storage |
| `om_ai/data_engine/improvement/improver.py` | OM Automated Dataset Improvement Agent |
| `om_ai/data_engine/improvement/rewriter.py` | OM Dataset Sample Rewriter Improves weak samples. |
| `om_ai/data_engine/intelligence/curriculum.py` | OM Curriculum Builder |
| `om_ai/data_engine/intelligence/difficulty.py` | OM Training Difficulty Detector |
| `om_ai/data_engine/intelligence/domain_classifier.py` | OM Training Domain Classifier |
| `om_ai/data_engine/intelligence/engine.py` | OM Training Data Intelligence Engine |
| `om_ai/data_engine/intelligence/skill_mapper.py` | OM Skill Mapping Engine |
| `om_ai/data_engine/pipeline/__init__.py` | OM Data Engine Pipeline Provides production data processing components: - Text cleaning - Duplicate detection - Quality  |
| `om_ai/data_engine/pipeline/chunker.py` | OM-1.0 Document Chunking Engine Splits large documents into AI training/RAG friendly chunks. |
| `om_ai/data_engine/pipeline/classifier.py` | OM Data Engine Knowledge Classification |
| `om_ai/data_engine/pipeline/cleaner.py` | OM Data Engine Text Cleaning Pipeline |
| `om_ai/data_engine/pipeline/dataset_builder.py` | OM-1.0 Data Engine Dataset Builder Production pipeline: Connector / ↓ Cleaning / ↓ Deduplication / ↓ Quality Evaluation  |
| `om_ai/data_engine/pipeline/deduplicator.py` | OM Data Engine Duplicate Removal |
| `om_ai/data_engine/pipeline/quality.py` | OM Data Engine Quality Scoring |

### `om_ai/data_pipeline/` — Dedup, quality, language filters

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/data_pipeline/__init__.py` | OMAI data pipeline — Milestone 1 factory for OMAI-Corpus-v1. Thin, named stages over ``om_ai.corpus`` so the Own Model R |
| `om_ai/data_pipeline/cleaner.py` | Text cleaning stage. |
| `om_ai/data_pipeline/deduplicator.py` | Exact-hash deduplication. |
| `om_ai/data_pipeline/downloader.py` | Download / fetch licensed sources into OMAI-Corpus-v1. |
| `om_ai/data_pipeline/language_filter.py` | Language detection / allow-list filter. |
| `om_ai/data_pipeline/pipeline.py` | End-to-end OMAI-Corpus-v1 pipeline runner. |
| `om_ai/data_pipeline/quality_score.py` | Document quality scoring. |
| `om_ai/data_pipeline/tokenizer.py` | Corpus tokenization helpers (production OM tokenizer). |
| `om_ai/data_pipeline/validator.py` | Validate OMAI-Corpus-v1 layout + stage artifacts. |

### `om_ai/decision/` — Decision / risk / strategy engine

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/decision/__init__.py` |   init   |
| `om_ai/decision/engine.py` | OM Autonomous Decision Engine |
| `om_ai/decision/evaluator.py` | OM Decision Evaluation Engine |
| `om_ai/decision/option.py` | OM Decision Option Model |
| `om_ai/decision/risk.py` | OM Risk Analysis Engine |
| `om_ai/decision/selector.py` | OM Best Decision Selector |
| `om_ai/decision/strategy.py` | OM Strategic Planning Layer |

### `om_ai/device_control/` — Device connector / manager

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/device_control/__init__.py` |   init   |
| `om_ai/device_control/command.py` | OM Device Command System |
| `om_ai/device_control/connector.py` | OM Hardware Connector Layer Future integrations: - MQTT - REST APIs - GPIO - Arduino - Raspberry Pi |
| `om_ai/device_control/device.py` | OM Device Model |
| `om_ai/device_control/feedback.py` | OM Device Feedback Intelligence |
| `om_ai/device_control/gateway.py` | OM Device Gateway Controls communication between brain and devices. |
| `om_ai/device_control/manager.py` | OM Device Control Manager |
| `om_ai/device_control/memory.py` | OM Device Interaction Memory |
| `om_ai/device_control/permission.py` | OM Device Safety Permission Layer |

### `om_ai/diagnostics/` — Logging and system diagnostics

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/diagnostics/__init__.py` | OM AI system diagnostics package. |
| `om_ai/diagnostics/logging_setup.py` | Application logging bootstrap for OM serve / doctor. |
| `om_ai/diagnostics/repair.py` | OM repair helpers — create missing folders / initialize empty DBs. |
| `om_ai/diagnostics/system_check.py` | system check |

### `om_ai/digital_twin/` — Digital twin simulation / optimizer

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/digital_twin/__init__.py` |   init   |
| `om_ai/digital_twin/entity.py` | OM Digital Twin Entity Model |
| `om_ai/digital_twin/manager.py` | OM Digital Twin Manager |
| `om_ai/digital_twin/memory.py` | OM Digital Twin Experience Memory |
| `om_ai/digital_twin/optimizer.py` | OM Digital Twin Optimization |
| `om_ai/digital_twin/prediction.py` | OM Digital Twin Prediction Engine |
| `om_ai/digital_twin/simulator.py` | OM Simulation Engine |
| `om_ai/digital_twin/state.py` | OM Digital Twin State Manager |
| `om_ai/digital_twin/twin.py` | OM Digital Twin Core |

### `om_ai/discovery/` — OpenAPI discovery tool

**3 Python files**

| Path | Role |
|------|------|
| `om_ai/discovery/__init__.py` |   init   |
| `om_ai/discovery/openapi.py` | openapi |
| `om_ai/discovery/project.py` | ProjectDiscovery: scan an authorized root path and return a structured project map. Security: - Only scans paths that ar |

### `om_ai/enterprise/` — Enterprise platform features

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/enterprise/__init__.py` | Enterprise facade — orgs, roles, API keys, usage, monitoring (wraps tenancy/security). |

### `om_ai/eval/` — Evaluation harness

**5 Python files**

| Path | Role |
|------|------|
| `om_ai/eval/__init__.py` |   init   |
| `om_ai/eval/benchmarks.py` | benchmarks |
| `om_ai/eval/chatgpt_compare.py` | chatgpt compare |
| `om_ai/eval/platform.py` | OM Evaluation Platform — measure reasoning, coding, math, knowledge, safety, agents. |
| `om_ai/eval/runner.py` | runner |

### `om_ai/evaluation/` — Evaluation services / runners

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/evaluation/__init__.py` | Evaluation framework — scorer + reports + improvement hooks. |
| `om_ai/evaluation/knowledge_confidence.py` | OM Knowledge Confidence Engine Checks: - Retrieval quality - Source quality - Context availability - Answer confidence |
| `om_ai/evaluation/online.py` | Online response evaluation — correctness, completeness, relevance, safety, quality. |
| `om_ai/evaluation/self_checker.py` | OM-1.0 Self Evaluation Engine Checks generated answers before sending to the user. |

### `om_ai/foundation/` — Foundation platform APIs glue

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/foundation/__init__.py` | Foundation upgrade — folders, DBs, configs, tests, report. |

### `om_ai/generation/` — Generation helpers

**2 Python files**

| Path | Role |
|------|------|
| `om_ai/generation/__init__.py` | OM Generation package. |
| `om_ai/generation/engine.py` | OM Generation Engine — real content via shared answer builder (no stubs). |

### `om_ai/genesis/` — Genesis corpus / platform bootstrap

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/genesis/__init__.py` | OM-1.0 Genesis-JARVIS intelligence training package. |
| `om_ai/genesis/domains.py` | domains |
| `om_ai/genesis/generator.py` | generator |
| `om_ai/genesis/templates.py` | Build structured OM-1.0 Genesis assistant answers. |

### `om_ai/goals/` — Goal storage and tracking

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/goals/__init__.py` |   init   |
| `om_ai/goals/goal.py` | OM Autonomous Goal Model |
| `om_ai/goals/manager.py` | OM Autonomous Goal Manager |
| `om_ai/goals/milestone.py` | OM Goal Milestone |
| `om_ai/goals/progress.py` | OM Goal Progress Engine |
| `om_ai/goals/scheduler.py` | OM Long Running Task Scheduler |
| `om_ai/goals/storage.py` | OM Persistent Goal Storage |

### `om_ai/hardware/` — Hardware sensor abstractions

**10 Python files**

| Path | Role |
|------|------|
| `om_ai/hardware/__init__.py` |   init   |
| `om_ai/hardware/actuator.py` | OM Actuator Control Layer |
| `om_ai/hardware/controller.py` | OM Embedded Controller Interface Future: Arduino ESP32 Raspberry Pi Custom Boards |
| `om_ai/hardware/device.py` | OM Hardware Device Model |
| `om_ai/hardware/driver.py` | OM Hardware Driver System |
| `om_ai/hardware/gateway.py` | OM Hardware Gateway Central communication layer. |
| `om_ai/hardware/manager.py` | OM Hardware Integration Manager |
| `om_ai/hardware/monitoring.py` | OM Hardware Monitoring System |
| `om_ai/hardware/protocol.py` | OM Hardware Communication Protocol |
| `om_ai/hardware/sensor.py` | OM Sensor Intelligence Layer |

### `om_ai/hardware_design/` — Hardware design memory / components

**10 Python files**

| Path | Role |
|------|------|
| `om_ai/hardware_design/__init__.py` |   init   |
| `om_ai/hardware_design/architecture.py` | OM Hardware Architecture Designer |
| `om_ai/hardware_design/circuit.py` | OM Circuit Design Foundation |
| `om_ai/hardware_design/component.py` | OM Component Selection Intelligence |
| `om_ai/hardware_design/manager.py` | OM Autonomous Hardware Design Manager |
| `om_ai/hardware_design/memory.py` | OM Hardware Design Experience Memory |
| `om_ai/hardware_design/optimization.py` | OM Hardware Optimization Intelligence |
| `om_ai/hardware_design/requirement.py` | OM Hardware Requirement Intelligence |
| `om_ai/hardware_design/simulation.py` | OM Hardware Simulation Engine |
| `om_ai/hardware_design/validation.py` | OM Hardware Validation Layer |

### `om_ai/identity/` — Identity helpers

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/identity/__init__.py` | OM (Operating Mind) — Genesis Intelligence Architecture identity. Canonical system identity used by Absolute OS + chat.  |

### `om_ai/improvement/` — Improvement queue / trainer jobs

**10 Python files**

| Path | Role |
|------|------|
| `om_ai/improvement/__init__.py` | OM Self-Improvement Engine — answer → score → weakness → dataset → train queue. |
| `om_ai/improvement/data_generator.py` | Generate SFT/preference training rows from weaknesses. |
| `om_ai/improvement/dataset_writer.py` | OM SFT Dataset Writer Stores training examples as JSONL. |
| `om_ai/improvement/evaluator.py` | Score an OM answer for structure, clarity, security, and task fit. |
| `om_ai/improvement/example.py` | OM Training Example Model Creates SFT training samples. |
| `om_ai/improvement/generator.py` | OM Training Example Generator Converts successful OM experiences into SFT training examples. |
| `om_ai/improvement/quality.py` | OM Knowledge Improvement Engine |
| `om_ai/improvement/trainer_queue.py` | Queue future SFT/DPO jobs from improvement examples. |
| `om_ai/improvement/version_manager.py` | Track OM software/intelligence versions after improvement cycles. |
| `om_ai/improvement/weakness_detector.py` | Detect weak areas from evaluation scores. |

### `om_ai/integrations/` — External integration plugins

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/integrations/__init__.py` |   init   |
| `om_ai/integrations/http_connector.py` | http connector |
| `om_ai/integrations/plugin.py` | plugin |
| `om_ai/integrations/whatsapp.py` | whatsapp |

### `om_ai/intelligence/` — Intelligence routing helpers

**12 Python files**

| Path | Role |
|------|------|
| `om_ai/intelligence/__init__.py` | OM Dynamic Intelligence Pipeline — understand → reason → generate → verify. |
| `om_ai/intelligence/agent_selector.py` | Dynamic agent selection from task requirements — not keyword→agent locks. |
| `om_ai/intelligence/context_engine.py` | Conversation / project context before answering. |
| `om_ai/intelligence/intelligence_manager.py` | Orchestrates the dynamic intelligence pipeline. |
| `om_ai/intelligence/intent_reasoner.py` | Dynamic intent reasoning — discovers intents beyond a fixed enum. |
| `om_ai/intelligence/knowledge_router.py` | Route to knowledge *sources* by domain — never spawn MusicAgent/DateAgent/etc. |
| `om_ai/intelligence/memory_retriever.py` | Retrieve relevant memory slices without topic-specific handlers. |
| `om_ai/intelligence/quality_evaluator.py` | Quality gate — regenerate if score < threshold. |
| `om_ai/intelligence/reasoning_engine.py` | Internal plan: Understand → Solve → Verify → Respond. |
| `om_ai/intelligence/response_planner.py` | Plan response style, then draft ONLY from real knowledge / reasoning / model. |
| `om_ai/intelligence/tool_selector.py` | Decide which tools are needed — capability inference, not manual maps. |
| `om_ai/intelligence/understanding_engine.py` | Deep understanding — semantic-style feature extraction (regex = helper signal only). |

### `om_ai/internet/` — Internet intelligence stubs

**2 Python files**

| Path | Role |
|------|------|
| `om_ai/internet/__init__.py` | STEP 87 — OM Internet Intelligence Layer. |
| `om_ai/internet/intelligence.py` | STEP 87 — OM Internet Intelligence Layer Controlled internet understanding: Web Search → Retrieval → Website Understandi |

### `om_ai/knowledge/` — RAG knowledge base: ingest, chunk, retrieve, graph RAG

**35 Python files**

| Path | Role |
|------|------|
| `om_ai/knowledge/__init__.py` |   init   |
| `om_ai/knowledge/brain.py` | STEP 88 — OM Advanced Knowledge Brain Information → Understanding → Knowledge Graph → Memory → Reasoning |
| `om_ai/knowledge/context_filter.py` | context filter |
| `om_ai/knowledge/corpus.py` | Knowledge corpus layout helpers (science/engineering/... buckets). |
| `om_ai/knowledge/dataset_cleaner.py` | OM Dataset Cleaner Removes low quality knowledge before ingestion. |
| `om_ai/knowledge/document_store.py` | OM Knowledge Document Store Stores large scale knowledge documents. Designed for: - RAG - Training datasets - Research c |
| `om_ai/knowledge/embeddings.py` | Local hashed embeddings + metadata vector index (no cloud embed API). |
| `om_ai/knowledge/engine.py` | Knowledge engine status + ingest facade for production CLI. |
| `om_ai/knowledge/factory.py` | Knowledge Factory — ingest → classify → chunk → embed/index → graph. |
| `om_ai/knowledge/facts.py` | High-precision local facts (not a substitute for ingested corpora). |
| `om_ai/knowledge/graph/__init__.py` | OM AI Knowledge Graph Engine This module provides: - Entity representation - Relationship mapping - Knowledge graph stor |
| `om_ai/knowledge/graph/engine.py` | engine |
| `om_ai/knowledge/graph/entity.py` | entity |
| `om_ai/knowledge/graph/models.py` | models |
| `om_ai/knowledge/graph/relation.py` | relation |
| `om_ai/knowledge/graph/store.py` | store |
| `om_ai/knowledge/graph.py` | Lightweight knowledge graph for OM foundation (JSON-backed). |
| `om_ai/knowledge/graph_rag/__init__.py` |   init   |
| `om_ai/knowledge/graph_rag/context_expander.py` | OM Knowledge Graph RAG Expansion Engine |
| `om_ai/knowledge/graph_rag/graph_retriever.py` | OM Knowledge Graph Retriever Finds related concepts from graph. |
| `om_ai/knowledge/graph_rag/merger.py` | OM Context Merger Combines RAG + Graph knowledge. |
| `om_ai/knowledge/index.py` | OM Knowledge Index Manages searchable knowledge references. |
| `om_ai/knowledge/ingestion/__init__.py` | Document ingestion: load → clean → chunk → metadata. |
| `om_ai/knowledge/processing/chunker.py` | OM Knowledge Chunker Splits large documents into searchable pieces. |
| `om_ai/knowledge/processing/embedder.py` | OM Embedding Engine Interface Later connect: - sentence transformers - local embedding models - custom OM embeddings |
| `om_ai/knowledge/quality_filter.py` | OM Knowledge Quality Filter Rejects incorrect / training-template knowledge before it reaches the user. |
| `om_ai/knowledge/rag.py` | rag |
| `om_ai/knowledge/ranker.py` | ranker |
| `om_ai/knowledge/retrieval/__init__.py` | Vector knowledge layer — wraps PersistentKnowledgeBase + local corpus index. |
| `om_ai/knowledge/retrieval/hybrid_retriever.py` | OM Hybrid Retriever Combines: 1. Vector similarity 2. Keyword matching 3. Metadata filtering |
| `om_ai/knowledge/retrieval/keyword_search.py` | OM Keyword Search Engine Exact keyword matching layer. |
| `om_ai/knowledge/retrieval/vector_retriever.py` | OM Vector Retriever Connects: Question ↓ Embedding ↓ Vector Store ↓ Relevant Knowledge |
| `om_ai/knowledge/selector.py` | Knowledge Selection System — keep what matters for the user's goal. |
| `om_ai/knowledge/storage/vector_store.py` | vector store |
| `om_ai/knowledge/vector_layer.py` | vector layer |

### `om_ai/knowledge_brain/` — Era-based knowledge brain (1600–2026)

**6 Python files**

| Path | Role |
|------|------|
| `om_ai/knowledge_brain/__init__.py` | OM Universal Knowledge Brain (1600–2026) — corpus + directive package. Honest scope: this builds a *knowledge ecosystem* |
| `om_ai/knowledge_brain/catalog.py` | Combined catalog for OM Knowledge Brain. |
| `om_ai/knowledge_brain/corpus.py` | corpus |
| `om_ai/knowledge_brain/directive.py` | OM-1.0 Genesis Universal Intelligence — master system directive. |
| `om_ai/knowledge_brain/domains.py` | Knowledge domains for OM Universal Knowledge Brain. |
| `om_ai/knowledge_brain/eras.py` | Historical eras for OM Knowledge Brain (1600–2026). |

### `om_ai/knowledge_graph/` — Knowledge graph engine

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/knowledge_graph/__init__.py` |   init   |
| `om_ai/knowledge_graph/engine.py` | OM Knowledge Graph Engine |
| `om_ai/knowledge_graph/entity.py` | OM Knowledge Graph Entity |
| `om_ai/knowledge_graph/extractor.py` | OM Advanced Entity Extraction Engine Responsible for: - Entity Detection - Entity Classification - Relationship Discover |
| `om_ai/knowledge_graph/graph_store.py` | OM Local Knowledge Graph Storage |
| `om_ai/knowledge_graph/relation.py` | OM Knowledge Relationship |
| `om_ai/knowledge_graph/storage.py` | OM Knowledge Graph Storage |

### `om_ai/knowledge_universe/` — Knowledge universe aggregation

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/knowledge_universe/__init__.py` | OM Universal Knowledge Universe — massive corpus layout + ingest hooks. Folders match the completion roadmap (books, pap |

### `om_ai/language/` — Language / response language helpers

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/language/__init__.py` | OM AI Universal Language Intelligence |
| `om_ai/language/analyzer.py` | OM AI Language Analyzer Analyzes user language context. |
| `om_ai/language/detector.py` | Detect user language (script + langdetect fallback). |
| `om_ai/language/manager.py` | OM AI Universal Language Manager Main controller for language intelligence. |
| `om_ai/language/meaning.py` | OM Multilingual Knowledge Intelligence (STEP 80.12) Language → Meaning → Knowledge Retrieval → Reasoning → Same-Language |
| `om_ai/language/response_language.py` | OM AI Response Language Controller Controls / verifies final answer language. |
| `om_ai/language/translator.py` | OM AI Language Translator Handles optional language conversion. |

### `om_ai/learning/` — Learning extractors / loops

**5 Python files**

| Path | Role |
|------|------|
| `om_ai/learning/__init__.py` | Learning layer — feedback → quality → datasets → improvement queue. |
| `om_ai/learning/experience.py` | OM Experience Model Stores successful and failed executions. |
| `om_ai/learning/extractor.py` | OM Experience Extractor Converts execution result into memory. |
| `om_ai/learning/learner.py` | OM Long Term Learning Engine |
| `om_ai/learning/pattern_store.py` | OM Pattern Storage Local persistent learning memory. |

### `om_ai/legacy/` — Legacy Ollama stubs (not production path)

**3 Python files**

| Path | Role |
|------|------|
| `om_ai/legacy/__init__.py` | Legacy adapters — connected to serve via connectivity_bridge (opt-in Ollama). |
| `om_ai/legacy/ollama/__init__.py` | Legacy Ollama HTTP client (opt-in only). Not used by ``om-ai serve`` / ``om_native`` production. Import explicitly: from |
| `om_ai/legacy/ollama/client.py` | Legacy Ollama chat client — explicit import only; never auto-wired into serve. |

### `om_ai/live_knowledge/` — HTTP/search live retrieval (not another LLM)

**11 Python files**

| Path | Role |
|------|------|
| `om_ai/live_knowledge/__init__.py` | OM live knowledge — retrieval infrastructure, not an LLM. |
| `om_ai/live_knowledge/crawler.py` | Authorized single-host document fetch for live-knowledge ingestion. This is not a general web spider. It fetches one app |
| `om_ai/live_knowledge/engine.py` | engine |
| `om_ai/live_knowledge/fetcher.py` | HTTP fetch for live knowledge (deterministic retrieval, not an LLM). |
| `om_ai/live_knowledge/freshness.py` | Freshness routing — decide when live retrieval should run (not an LLM). |
| `om_ai/live_knowledge/html_text.py` | Deterministic HTML → plain text (no LLM). |
| `om_ai/live_knowledge/index.py` | Local document index helpers for live knowledge. |
| `om_ai/live_knowledge/router.py` | Wire freshness → real retrieval → context for OM-1.0 (never another LLM). |
| `om_ai/live_knowledge/search.py` | Local lexical search (BM25-lite) — no external embeddings / no LLM. |
| `om_ai/live_knowledge/sources.py` | Configured live knowledge sources (URLs / local docs). Not LLM providers. |
| `om_ai/live_knowledge/web_search.py` | Public web search helpers — HTTP retrieval only, never an LLM API. |

### `om_ai/memory/` — SQLite memory + conversation stores

**20 Python files**

| Path | Role |
|------|------|
| `om_ai/memory/__init__.py` | OM Memory package — short/long/episodic/semantic + layered SQLite. |
| `om_ai/memory/conversation.py` | OM-1.0 Conversation Memory Stores and retrieves conversation history. Purpose: - Keep chat context - Maintain previous q |
| `om_ai/memory/conversations.py` | conversations |
| `om_ai/memory/episodic_memory.py` | OM Episodic Memory — experience of past Q→A / task outcomes. |
| `om_ai/memory/experience.py` | OM Experience Memory Stores successful reasoning patterns. |
| `om_ai/memory/extractor.py` | Extract useful memories from conversations. |
| `om_ai/memory/layers.py` | Layered memory API over SQLiteMemoryStore (additive, non-breaking). |
| `om_ai/memory/long_term.py` | OM Long Term Memory Permanent AI memory storage. |
| `om_ai/memory/manager.py` | OM Memory Manager Controls: - Store - Recall - Long term memory |
| `om_ai/memory/memory_manager.py` | OM Advanced Memory Manager (STEP 80.13) Short Term + Long Term + Personal/Semantic + Episodic/Experience + Learning Stru |
| `om_ai/memory/memory_scoring.py` | memory scoring |
| `om_ai/memory/models.py` | OM Memory Data Models |
| `om_ai/memory/project_extractor.py` | Extract project related memories. |
| `om_ai/memory/project_memory.py` | OM Project Memory Stores project state and development context. |
| `om_ai/memory/semantic_memory.py` | OM Semantic Memory — personal knowledge / facts / preferences. |
| `om_ai/memory/semantic_search.py` | Semantic Memory Retrieval Finds relevant memories. |
| `om_ai/memory/session.py` | Session memory — short-term window + durable preference/project writes. |
| `om_ai/memory/short_term.py` | OM Short Term Memory Stores current reasoning context. |
| `om_ai/memory/sqlite_memory.py` | sqlite memory |
| `om_ai/memory/storage.py` | OM Persistent Memory Storage SQLite based memory database. |

### `om_ai/memory_intelligence/` — Memory importance / extraction

**6 Python files**

| Path | Role |
|------|------|
| `om_ai/memory_intelligence/__init__.py` | OM Memory Intelligence package. |
| `om_ai/memory_intelligence/consolidator.py` | OM Autonomous Memory Consolidation Engine |
| `om_ai/memory_intelligence/experience.py` | OM Experience Memory Model |
| `om_ai/memory_intelligence/extractor.py` | OM Experience Knowledge Extractor |
| `om_ai/memory_intelligence/importance.py` | OM Memory Importance Scoring |
| `om_ai/memory_intelligence/storage.py` | OM Permanent Experience Storage |

### `om_ai/model/` — OMTransformer decoder-only architecture

**10 Python files**

| Path | Role |
|------|------|
| `om_ai/model/__init__.py` |   init   |
| `om_ai/model/attention.py` | Attention modules (roadmap layout). |
| `om_ai/model/causal_loss.py` | Causal language-modeling loss for OM chat / pretrain (assistant-only masking). Labels use ``ignore_index=-100`` for padd |
| `om_ai/model/config.py` | Model config re-export (roadmap: om-ai-model/config). |
| `om_ai/model/embeddings.py` | Token + positional embeddings (RoPE applied in attention). |
| `om_ai/model/feedforward.py` | Feed-forward / SwiGLU. |
| `om_ai/model/model.py` | Top-level model export (roadmap: model/model.py). |
| `om_ai/model/normalization.py` | Normalization modules. |
| `om_ai/model/rope.py` | rope |
| `om_ai/model/transformer.py` | transformer |

### `om_ai/model_intelligence/` — Model lifecycle / finetune / monitor

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/model_intelligence/__init__.py` |   init   |
| `om_ai/model_intelligence/adapter.py` | OM Model Adapter System Future connection: LoRA QLoRA Adapters |
| `om_ai/model_intelligence/deployment.py` | OM Model Deployment Layer |
| `om_ai/model_intelligence/evaluator.py` | OM Model Evaluation Intelligence |
| `om_ai/model_intelligence/finetune.py` | OM Fine Tuning Controller Future: PyTorch Transformers Accelerate |
| `om_ai/model_intelligence/manager.py` | OM Model Intelligence Manager |
| `om_ai/model_intelligence/model.py` | OM Model Definition Represents model versions and capabilities. |
| `om_ai/model_intelligence/monitor.py` | OM Model Runtime Monitoring |
| `om_ai/model_intelligence/registry.py` | OM Model Version Registry |

### `om_ai/multimodal/` — Image/audio/video/document multimodal stack

**23 Python files**

| Path | Role |
|------|------|
| `om_ai/multimodal/__init__.py` | STEP 89 — OM Multimodal Intelligence Fusion Combine text + image + PDF (+ audio/video stubs) into one understanding pack |
| `om_ai/multimodal/agent.py` | OM Multimodal Intelligence Agent |
| `om_ai/multimodal/audio_engine.py` | Audio understanding stub with real file validation. |
| `om_ai/multimodal/context.py` | OM Multimodal Context Builder |
| `om_ai/multimodal/document/__init__.py` | Multimodal document module alias. |
| `om_ai/multimodal/document_ai.py` | Document AI — text/PDF/docx understanding without vision weights. |
| `om_ai/multimodal/document_engine.py` | Document understanding (PDF/text/code files). |
| `om_ai/multimodal/fusion.py` | OM Multimodal Feature Fusion Engine |
| `om_ai/multimodal/image/__init__.py` | Image modality stub. |
| `om_ai/multimodal/image_engine.py` | Image validation + visual structure understanding. |
| `om_ai/multimodal/input.py` | OM Multimodal Input Model |
| `om_ai/multimodal/input_router.py` | Route any input blob to the right modality engine — by content signals, not topic keywords. |
| `om_ai/multimodal/manager.py` | Multimodal Intelligence Manager Any Input → route → modality engines → vision reasoning → structured packet |
| `om_ai/multimodal/memory.py` | OM Multimodal Experience Memory |
| `om_ai/multimodal/ocr_engine.py` | OCR extraction with optional engines; never crashes the server. |
| `om_ai/multimodal/orchestrator.py` | orchestrator |
| `om_ai/multimodal/router.py` | OM Modality Router |
| `om_ai/multimodal/understanding.py` | OM Unified Multimodal Understanding Engine |
| `om_ai/multimodal/video/__init__.py` | Video modality stub — not implemented yet. |
| `om_ai/multimodal/video_engine.py` | Video understanding stub with metadata. |
| `om_ai/multimodal/vision/__init__.py` | Vision modality package (weights external). |
| `om_ai/multimodal/vision_reasoning.py` | Answer vision questions from image analysis packets. |
| `om_ai/multimodal/voice/__init__.py` | Voice modality package (weights external). |

### `om_ai/observability/` — Metrics, health, events

**6 Python files**

| Path | Role |
|------|------|
| `om_ai/observability/__init__.py` | OM AI observability package. Exports ------- TrainingMetricsLogger – thread-safe JSONL metrics appender for training run |
| `om_ai/observability/analyzer.py` | OM Performance Analyzer |
| `om_ai/observability/events.py` | OM System Event Tracker |
| `om_ai/observability/health.py` | OM Health Monitor |
| `om_ai/observability/metrics.py` | metrics |
| `om_ai/observability/monitor.py` | OM Self Monitoring Engine |

### `om_ai/operating_intelligence/` — OI facade, cycles, embodiment bridges

**23 Python files**

| Path | Role |
|------|------|
| `om_ai/operating_intelligence/__init__.py` | OM AI Operating Intelligence — Absolute Cognitive OS facade. |
| `om_ai/operating_intelligence/agent_bridge.py` | Agent civilization bridge — route to specialist agent roles. |
| `om_ai/operating_intelligence/cognition_bridge.py` | Cognition bridge — understand → decompose → plan → solve → verify → reflect. |
| `om_ai/operating_intelligence/core.py` | OM Operating Intelligence Core Central brain coordinator. |
| `om_ai/operating_intelligence/embodiment/__init__.py` | Physical / IoT embodiment contracts — stubs until real drivers exist. |
| `om_ai/operating_intelligence/embodiment/electronics.py` | Electronics / MCU / IoT control contract (stub). |
| `om_ai/operating_intelligence/embodiment/gateway.py` | IoT gateway contract (stub). |
| `om_ai/operating_intelligence/embodiment/robotics.py` | Robotics control contract (stub — simulate before physical). |
| `om_ai/operating_intelligence/embodiment/sensors.py` | Sensor ingest contract (stub). |
| `om_ai/operating_intelligence/embodiment/twin.py` | Digital twin contract (stub). |
| `om_ai/operating_intelligence/facade.py` | facade |
| `om_ai/operating_intelligence/growth_bridge.py` | Growth bridge — evaluate → weakness → training examples (self-improvement). |
| `om_ai/operating_intelligence/health.py` | OM System Health Monitor |
| `om_ai/operating_intelligence/knowledge_bridge.py` | Knowledge bridge — RAG + dataset brain + fact table + vector index. |
| `om_ai/operating_intelligence/manager.py` | OM Operating Intelligence Manager Main integration layer. |
| `om_ai/operating_intelligence/memory.py` | OM Global Intelligence Memory |
| `om_ai/operating_intelligence/memory_bridge.py` | Memory bridge — multi-layer human-like memory for Absolute OS. |
| `om_ai/operating_intelligence/module_registry.py` | OM Intelligence Module Registry |
| `om_ai/operating_intelligence/neural_simulation.py` | Digital neural simulation — adaptive memory graph (safe bio-inspired layer). |
| `om_ai/operating_intelligence/orchestrator.py` | OM Intelligence Orchestrator Coordinates all intelligence modules. |
| `om_ai/operating_intelligence/perception_bridge.py` | Perception bridge — voice / vision / multimodal (null-safe). |
| `om_ai/operating_intelligence/state.py` | OM Global Intelligence State |
| `om_ai/operating_intelligence/universal.py` | universal |

### `om_ai/orchestration/` — Execution plans and orchestration

**5 Python files**

| Path | Role |
|------|------|
| `om_ai/orchestration/__init__.py` |   init   |
| `om_ai/orchestration/context_builder.py` | OM Context Builder Combines all intelligence sources. |
| `om_ai/orchestration/execution_plan.py` | OM Execution Plan Defines agent execution flow. |
| `om_ai/orchestration/orchestrator.py` | OM Agent Knowledge Tool Orchestrator Central execution controller. |
| `om_ai/orchestration/result.py` | OM Orchestration Result |

### `om_ai/perception/` — Vision/OCR/PDF perception stack

**28 Python files**

| Path | Role |
|------|------|
| `om_ai/perception/document/document_detector.py` | document detector |
| `om_ai/perception/document/models.py` | models |
| `om_ai/perception/document/pdf/__init__.py` | OM AI PDF Semantic Understanding Module Provides semantic analysis capabilities for PDF documents: - Document classifica |
| `om_ai/perception/document/pdf/manager.py` | manager |
| `om_ai/perception/document/pdf/models.py` | models |
| `om_ai/perception/document/pdf/pdf_engine.py` | pdf engine |
| `om_ai/perception/document/pdf/pdf_image_extractor.py` | pdf image extractor |
| `om_ai/perception/document/pdf/pdf_metadata.py` | pdf metadata |
| `om_ai/perception/document/pdf/pdf_reader.py` | pdf reader |
| `om_ai/perception/document/pdf/pdf_structure.py` | pdf structure |
| `om_ai/perception/document/pdf/pdf_table_extractor.py` | pdf table extractor |
| `om_ai/perception/document/pdf/semantic/__init__.py` |   init   |
| `om_ai/perception/document/pdf/semantic/classifier.py` | classifier |
| `om_ai/perception/document/pdf/semantic/entity_extractor.py` | Extract simple domain entities from PDF text. |
| `om_ai/perception/document/pdf/semantic/insight_engine.py` | Generate insights from extracted PDF entities. |
| `om_ai/perception/document/pdf/semantic/semantic_engine.py` | OM AI PDF Semantic Understanding Engine Responsible for: - Document classification - Entity extraction - Insight generat |
| `om_ai/perception/document/pdf_reader.py` | pdf reader |
| `om_ai/perception/input_detector.py` | input detector |
| `om_ai/perception/input_gateway.py` | input gateway |
| `om_ai/perception/models.py` | models |
| `om_ai/perception/ocr/models.py` | models |
| `om_ai/perception/ocr/ocr_engine.py` | ocr engine |
| `om_ai/perception/perception_manager.py` | perception manager |
| `om_ai/perception/vision/image_analyzer.py` | image analyzer |
| `om_ai/perception/vision/manager.py` | manager |
| `om_ai/perception/vision/models.py` | models |
| `om_ai/perception/vision/object_detector.py` | object detector |
| `om_ai/perception/vision/vision_engine.py` | vision engine |

### `om_ai/physical_reasoning/` — Physics / causal / object-state reasoning

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/physical_reasoning/__init__.py` |   init   |
| `om_ai/physical_reasoning/causal_reasoning.py` | OM Cause Effect Reasoning |
| `om_ai/physical_reasoning/decision.py` | OM Physical Decision Engine |
| `om_ai/physical_reasoning/manager.py` | OM Human-Level Physical Reasoning Manager |
| `om_ai/physical_reasoning/memory.py` | OM Physical Experience Memory |
| `om_ai/physical_reasoning/object_state.py` | OM Object State Intelligence |
| `om_ai/physical_reasoning/physics_model.py` | OM Physics World Model Understands: - gravity - stability - movement - interaction |
| `om_ai/physical_reasoning/prediction_engine.py` | OM Future Physical State Prediction |
| `om_ai/physical_reasoning/relation_engine.py` | OM Physical Relationship Engine |

### `om_ai/platform/` — Platform package marker

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/platform/__init__.py` | OM Enterprise Platform builder — creates layout + verifies services. |

### `om_ai/rag/` — RAG relevance helpers

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/rag/relevance_checker.py` | relevance checker |

### `om_ai/reasoning/` — Planner + reasoning engine

**3 Python files**

| Path | Role |
|------|------|
| `om_ai/reasoning/__init__.py` |   init   |
| `om_ai/reasoning/engine.py` | Advanced reasoning architecture for OM (software layer). Delegates to the foundation pipeline for rich domain solutions  |
| `om_ai/reasoning/planner.py` | Planning subsystem: deterministic RulePlanner + LLM-driven LLMPlanner. RulePlanner — keyword-heuristic baseline (no LLM  |

### `om_ai/recovery/` — Failure analysis / recovery strategies

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/recovery/__init__.py` |   init   |
| `om_ai/recovery/analyzer.py` | OM Failure Analysis Engine |
| `om_ai/recovery/executor.py` | OM Self Healing Execution Engine |
| `om_ai/recovery/failure.py` | OM Failure Event Model |
| `om_ai/recovery/memory.py` | OM Failure Learning Memory |
| `om_ai/recovery/root_cause.py` | OM Root Cause Analysis |
| `om_ai/recovery/strategy.py` | OM Recovery Strategy Engine |

### `om_ai/reflection/` — Self-reflection / critique

**5 Python files**

| Path | Role |
|------|------|
| `om_ai/reflection/__init__.py` |   init   |
| `om_ai/reflection/analyzer.py` | OM Failure Analysis Engine |
| `om_ai/reflection/engine.py` | OM Autonomous Improvement Engine |
| `om_ai/reflection/reflector.py` | OM Self Reflection Generator |
| `om_ai/reflection/strategy.py` | OM Strategy Improvement Storage |

### `om_ai/registry/` — Model registry

**2 Python files**

| Path | Role |
|------|------|
| `om_ai/registry/__init__.py` |   init   |
| `om_ai/registry/model_registry.py` | model registry |

### `om_ai/research/` — Research agent pipeline

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/research/__init__.py` |   init   |
| `om_ai/research/agent.py` | OM Research Intelligence Agent |
| `om_ai/research/analyzer.py` | OM Research Analysis Engine |
| `om_ai/research/autonomous.py` | Autonomous search decision — use research when knowledge is missing. |
| `om_ai/research/collector.py` | OM Information Collection Engine |
| `om_ai/research/memory.py` | OM Research Knowledge Memory |
| `om_ai/research/planner.py` | OM Research Planning Engine |
| `om_ai/research/summarizer.py` | OM Research Summary Generator |
| `om_ai/research/validator.py` | OM Research Fact Validation |

### `om_ai/response_engine/` — Formatting, streaming, emotion style

**5 Python files**

| Path | Role |
|------|------|
| `om_ai/response_engine/__init__.py` | OM AI Response Experience Engine — format, markdown, style, streaming helpers. This is the Experience Layer (not the fou |
| `om_ai/response_engine/emotion_style.py` | Emotion / experience style helpers for OM chat. |
| `om_ai/response_engine/formatter.py` | Structure raw model / fallback text into readable assistant blocks. |
| `om_ai/response_engine/markdown_parser.py` | Lightweight markdown → safe HTML (server-side helper; UI has its own renderer). |
| `om_ai/response_engine/stream_manager.py` | Streaming helpers — chunk text for SSE / progressive UI. |

### `om_ai/robotics/` — Robotics manager / actuators / sensors

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/robotics/__init__.py` |   init   |
| `om_ai/robotics/actuator.py` | OM Robot Actuator Layer |
| `om_ai/robotics/controller.py` | OM Robot Controller |
| `om_ai/robotics/learning.py` | OM Robot Experience Learning |
| `om_ai/robotics/manager.py` | OM Robotics Intelligence Manager |
| `om_ai/robotics/motion.py` | OM Robot Motion Intelligence |
| `om_ai/robotics/robot.py` | OM Robot Intelligence Model |
| `om_ai/robotics/sensor.py` | OM Robot Sensor System |

### `om_ai/runtime/` — Chat backend, orchestrator, external LLMs, engine

**13 Python files**

| Path | Role |
|------|------|
| `om_ai/runtime/__init__.py` |   init   |
| `om_ai/runtime/chat_backend.py` | chat backend |
| `om_ai/runtime/chat_orchestrator.py` | Chat orchestration: template + generation config + quality gate. |
| `om_ai/runtime/chat_pipeline.py` | chat pipeline |
| `om_ai/runtime/connectivity_bridge.py` | OM System Connectivity Bridge Connects previously orphaned / duplicate packages into the live chat/serve path. Nothing i |
| `om_ai/runtime/engine.py` | engine |
| `om_ai/runtime/evolution_matrix.py` | evolution matrix |
| `om_ai/runtime/external_llms.py` | external llms |
| `om_ai/runtime/intelligence.py` | intelligence |
| `om_ai/runtime/live_answer.py` | Live web + Wikipedia grounded answers for chat (no external LLM). |
| `om_ai/runtime/public_reply.py` | Public reply sanitizer — never leak internals to the user. Strips: Knowledge Brain, Memory dumps, Connected systems, too |
| `om_ai/runtime/session_flags.py` | Per-request feature flags from user Settings (overrides env defaults). |
| `om_ai/runtime/system_prompts.py` | Database-backed system prompts for OM chat orchestration. |

### `om_ai/safety/` — Safety policies / alignment / risk

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/safety/__init__.py` |   init   |
| `om_ai/safety/alignment.py` | OM Alignment Intelligence Checks whether actions match system objectives. |
| `om_ai/safety/audit.py` | OM Safety Audit System |
| `om_ai/safety/decision.py` | OM Safety Decision Engine |
| `om_ai/safety/manager.py` | OM Advanced Safety Manager |
| `om_ai/safety/memory.py` | OM Safety Learning Memory |
| `om_ai/safety/permission.py` | OM Permission Management |
| `om_ai/safety/policy.py` | OM Safety Policy Engine |
| `om_ai/safety/risk.py` | OM Risk Assessment Engine Analyzes potential danger before execution. |

### `om_ai/security/` — Auth, tokens, accounts, SSRF, audit, rate limits

**14 Python files**

| Path | Role |
|------|------|
| `om_ai/security/__init__.py` | OM AI security package. |
| `om_ai/security/accounts.py` | accounts |
| `om_ai/security/audit.py` | Append-only SQLite-backed audit log for OM AI. |
| `om_ai/security/audit_log.py` | OM Security file-backed audit logger (JSON). SQLite append-only history lives in ``om_ai.security.audit.AuditLog``. This |
| `om_ai/security/auth.py` | auth |
| `om_ai/security/controller.py` | OM Autonomous Security Controller Combines: - Policy validation - Permission checking - Sandbox execution - Audit loggin |
| `om_ai/security/permission.py` | OM Permission Manager |
| `om_ai/security/policy.py` | OM Security Policy Engine Defines allowed and blocked actions. |
| `om_ai/security/rate_limit.py` | In-memory sliding-window rate limiter for OM AI. |
| `om_ai/security/sandbox.py` | OM Sandbox Execution Layer Controls tool execution. |
| `om_ai/security/secrets.py` | Secret management and redaction utilities for OM AI. SecretStore reads secrets from environment variables only, never fr |
| `om_ai/security/session_cookie.py` | HttpOnly session cookie helpers for account auth. |
| `om_ai/security/ssrf.py` | SSRF protection guard for OM AI. Validates URLs before outbound HTTP calls to block requests to private, link-local, met |
| `om_ai/security/tokens.py` | tokens |

### `om_ai/self_improvement/` — Self-improvement engine

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/self_improvement/__init__.py` |   init   |
| `om_ai/self_improvement/analyzer.py` | OM Performance Analysis Engine Analyzes: - Task results - Agent performance - Quality scores |
| `om_ai/self_improvement/engine.py` | OM Autonomous Self Improvement Engine |
| `om_ai/self_improvement/evaluator.py` | OM Improvement Evaluation Engine |
| `om_ai/self_improvement/memory.py` | OM Self Improvement Memory |
| `om_ai/self_improvement/optimizer.py` | OM Strategy Optimization Engine |
| `om_ai/self_improvement/strategy.py` | OM Improvement Strategy Generator |
| `om_ai/self_improvement/weakness.py` | OM Weakness Detection Engine |

### `om_ai/software_agent/` — Code-modifying software agent

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/software_agent/__init__.py` |   init   |
| `om_ai/software_agent/agent.py` | OM Autonomous Software Engineering Agent |
| `om_ai/software_agent/change.py` | OM Code Change Model |
| `om_ai/software_agent/file_selector.py` | OM Intelligent File Selector |
| `om_ai/software_agent/memory.py` | OM Engineering Experience Memory |
| `om_ai/software_agent/modifier.py` | OM Code Modification Engine Safe placeholder layer. |
| `om_ai/software_agent/planner.py` | OM Software Change Planner |
| `om_ai/software_agent/reviewer.py` | OM Code Review Intelligence |

### `om_ai/system/` — System package marker

**1 Python files**

| Path | Role |
|------|------|
| `om_ai/system/__init__.py` |   init   |

### `om_ai/tenancy/` — Tenant directory

**2 Python files**

| Path | Role |
|------|------|
| `om_ai/tenancy/__init__.py` |   init   |
| `om_ai/tenancy/service.py` | service |

### `om_ai/testing/` — Internal testing agents / generators

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/testing/__init__.py` |   init   |
| `om_ai/testing/agent.py` | OM Autonomous QA Agent |
| `om_ai/testing/analyzer.py` | OM Code Quality Analyzer |
| `om_ai/testing/generator.py` | OM Autonomous Test Generator |
| `om_ai/testing/memory.py` | OM Testing Experience Memory |
| `om_ai/testing/quality.py` | OM Quality Evaluation |
| `om_ai/testing/runner.py` | OM Test Execution Engine |
| `om_ai/testing/test_case.py` | OM Test Case Model |

### `om_ai/tokenizer/` — Byte-BPE tokenizer

**4 Python files**

| Path | Role |
|------|------|
| `om_ai/tokenizer/__init__.py` |   init   |
| `om_ai/tokenizer/byte_bpe.py` | byte bpe |
| `om_ai/tokenizer/loader.py` | loader |
| `om_ai/tokenizer/omai_v1.py` | OMAI-Tokenizer-v1 special-token contract. Production weights currently use chat specials already in ``artifacts/tokenize |

### `om_ai/tools/` — Tool router, harvest CLI, security gates

**19 Python files**

| Path | Role |
|------|------|
| `om_ai/tools/__init__.py` | Tool registry facade over om_ai.actions (+ chat tool runner + action layer). |
| `om_ai/tools/base.py` | OM Tool Base Interface |
| `om_ai/tools/chat_runner.py` | chat runner |
| `om_ai/tools/code_tool.py` | Code Analysis Tool — real coding_brain call, not a stub. |
| `om_ai/tools/data_tool.py` | Data Processing Tool |
| `om_ai/tools/file_tool.py` | File Management Tool — safe read/list in workspace. |
| `om_ai/tools/intelligence/__init__.py` | STEP 86 — OM Tool Intelligence + Autonomous Action Layer User → Reasoning → Tool Decision → Permission → Execution → Ana |
| `om_ai/tools/intelligence/action_layer.py` | action layer |
| `om_ai/tools/intelligence/audit.py` | Action audit log — append-only JSONL for tool decisions and executions. |
| `om_ai/tools/intelligence/decision_engine.py` | decision engine |
| `om_ai/tools/intelligence/executor.py` | Action Executor — runs permitted tools via chat_runner + specialty handlers. |
| `om_ai/tools/intelligence/permission_gate.py` | Permission gate for autonomous tool actions. Risk levels: low — date, calculator, knowledge (always allowed when tools e |
| `om_ai/tools/intelligence/result_analyzer.py` | Result Analysis — decide if tool output is enough to answer, or retry/clarify. |
| `om_ai/tools/llm_harvest.py` | CLI helper: harvest teacher LLM answers into OM training JSONL. Example: .venv/bin/python -m om_ai.tools.llm_harvest \ - |
| `om_ai/tools/router.py` | OM Tool Router — select AND execute the best tool. |
| `om_ai/tools/security/__init__.py` |   init   |
| `om_ai/tools/security/permission.py` | Upgrade PermissionChecker to use ActionPermissionGate (STEP 86). |
| `om_ai/tools/security/safety_manager.py` | OM Tool Safety Manager Controls tool execution. |
| `om_ai/tools/security/validator.py` | OM Tool Risk Validator |

### `om_ai/training/` — Pretrain / SFT / DPO / PPO / 70B trainers

**20 Python files**

| Path | Role |
|------|------|
| `om_ai/training/__init__.py` |   init   |
| `om_ai/training/chatgpt_upgrade.py` | ChatGPT-parity upgrade roadmap for OM-1.0 (sampling → architecture → SFT → DPO). OM already ships RoPE + RMSNorm + SwiGL |
| `om_ai/training/checkpoint.py` | Checkpoint path helpers. |
| `om_ai/training/dataset_loader.py` | Training dataset helpers for OMAI-Corpus-v1. |
| `om_ai/training/deepspeed_train.py` | DeepSpeed ZeRO-3 entry for OMTransformer with partition-aware init. |
| `om_ai/training/distributed.py` | DDP / FSDP distributed training with optional meta-device partition-aware init. |
| `om_ai/training/dpo.py` | dpo |
| `om_ai/training/fix_and_check_om70b_mac.py` | fix and check om70b mac |
| `om_ai/training/local_knowledge.py` | Build knowledge.txt from local offline documentation folders (no internet). Pulls free text from paths on your Mac into  |
| `om_ai/training/om_tokenizer.py` | Self-contained BPE sub-word tokenizer for OM-1.0 (no Hugging Face). Groups characters into meaningful pieces (e.g. learn |
| `om_ai/training/partition_init.py` | Partition-aware model construction for 70B-scale training. Problem with the old DeepSpeed entrypoint: model = OMTransfor |
| `om_ai/training/ppo.py` | ppo |
| `om_ai/training/preference.py` | preference |
| `om_ai/training/preflight.py` | preflight |
| `om_ai/training/production_pipeline.py` | production pipeline |
| `om_ai/training/reward_model.py` | reward model |
| `om_ai/training/sft.py` | sft |
| `om_ai/training/train_70b.py` | OM-70B training launcher: preflight → distributed pretrain → SFT → preference → gates. This does **not** claim frontier  |
| `om_ai/training/train_om1.py` | OM-1.0 smoke / local training entry (truthful; not 70B). |
| `om_ai/training/trainer.py` | trainer |

### `om_ai/training_pipeline/` — Higher-level training pipeline registry

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/training_pipeline/__init__.py` |   init   |
| `om_ai/training_pipeline/dataset.py` | OM Training Dataset Storage |
| `om_ai/training_pipeline/evaluation.py` | OM Model Evaluation Dataset |
| `om_ai/training_pipeline/experience.py` | OM Training Experience Collector Collects: - Agent results - Workflow results - Research results - Failure recovery |
| `om_ai/training_pipeline/preference.py` | OM Preference Dataset Generator Used for DPO/RLHF style training. |
| `om_ai/training_pipeline/registry.py` | OM Model Version Registry |
| `om_ai/training_pipeline/sft.py` | Supervised Fine Tuning Dataset Generator |
| `om_ai/training_pipeline/trainer.py` | OM Training Pipeline Controller Future connection point: PyTorch Transformers Accelerate Distributed Training |

### `om_ai/understanding/` — Intent, typo, context, query kind

**10 Python files**

| Path | Role |
|------|------|
| `om_ai/understanding/__init__.py` | OM Cognitive Understanding Layer — meaning before generation. |
| `om_ai/understanding/context_analyzer.py` | Conversation / project context for meaning grounding. |
| `om_ai/understanding/context_engine.py` | Context Intelligence — conversation, project, preferences, prior decisions. |
| `om_ai/understanding/entities.py` | Contextual entity / acronym expansion (meaning, not word-for-word). |
| `om_ai/understanding/intent_detector.py` | Intent detection for Cognitive Understanding Layer. |
| `om_ai/understanding/language_brain.py` | Language Understanding Brain — meaning of words, not only the typed string. Pipeline: spelling → grammar → language dete |
| `om_ai/understanding/meaning_parser.py` | Parse clarified meaning / user goal from messy chat text. |
| `om_ai/understanding/query_kind.py` | OM Query Intelligence Classifier Classifies user requests before: - planning - retrieval - agent selection - response ge |
| `om_ai/understanding/typo_corrector.py` | Lightweight typo / slang normalizer (no external LLM). |
| `om_ai/understanding/understanding_pipeline.py` | OM Cognitive Understanding Layer v1 — meaning before generation. |

### `om_ai/universal_robotics/` — Universal robotics world model / skills

**9 Python files**

| Path | Role |
|------|------|
| `om_ai/universal_robotics/__init__.py` |   init   |
| `om_ai/universal_robotics/adaptation.py` | OM Robot Adaptation Intelligence |
| `om_ai/universal_robotics/manager.py` | OM Universal Robotics Intelligence Manager |
| `om_ai/universal_robotics/perception.py` | OM Robotic Perception Intelligence |
| `om_ai/universal_robotics/planning.py` | OM Universal Robot Planning Engine |
| `om_ai/universal_robotics/reasoning.py` | OM Physical Reasoning Engine |
| `om_ai/universal_robotics/robot_memory.py` | OM Universal Robot Memory |
| `om_ai/universal_robotics/skill_learning.py` | OM Robotic Skill Learning |
| `om_ai/universal_robotics/world_model.py` | OM Universal Robotics World Model |

### `om_ai/user_intelligence/` — User profile / preference graph

**7 Python files**

| Path | Role |
|------|------|
| `om_ai/user_intelligence/__init__.py` |   init   |
| `om_ai/user_intelligence/engine.py` | OM Personal Intelligence Engine |
| `om_ai/user_intelligence/entity.py` | OM Personal Knowledge Entity |
| `om_ai/user_intelligence/extractor.py` | OM User Intelligence Extractor |
| `om_ai/user_intelligence/graph.py` | OM Personal Knowledge Graph Storage |
| `om_ai/user_intelligence/preference.py` | OM User Preference Memory |
| `om_ai/user_intelligence/profile.py` | OM User Intelligence Profile |

### `om_ai/vision/` — Vision encoders / OCR / ViT

**12 Python files**

| Path | Role |
|------|------|
| `om_ai/vision/__init__.py` |   init   |
| `om_ai/vision/analyzer.py` | OM Vision Analysis Engine |
| `om_ai/vision/base.py` | base |
| `om_ai/vision/embedding.py` | OM Visual Embedding Foundation Future: CLIP Vision Transformer Multimodal Embeddings |
| `om_ai/vision/image_processor.py` | OM Image Processing Layer Handles: - Image loading - Metadata extraction - Basic preprocessing |
| `om_ai/vision/manager.py` | OM Vision Manager |
| `om_ai/vision/memory.py` | OM Vision Experience Memory |
| `om_ai/vision/multimodal.py` | multimodal |
| `om_ai/vision/object_detection.py` | OM Object Detection Engine Future: - YOLO - DETR - Vision Transformers |
| `om_ai/vision/ocr.py` | OM OCR Intelligence Layer Future integrations: - Tesseract - EasyOCR - PaddleOCR |
| `om_ai/vision/vision_agent.py` | OM Vision Intelligence Agent |
| `om_ai/vision/vit.py` | vit |

### `om_ai/voice/` — STT / TTS / voice commands

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/voice/__init__.py` | STEP 91 — OM Voice Intelligence System (controlled scaffold). Voice → STT → Understanding → Reasoning → TTS Uses local h |
| `om_ai/voice/audio_encoder.py` | audio encoder |
| `om_ai/voice/audio_memory.py` | OM Voice Interaction Memory |
| `om_ai/voice/base.py` | base |
| `om_ai/voice/speech_to_text.py` | OM Speech Recognition Layer Future integrations: - Whisper - Vosk - DeepSpeech |
| `om_ai/voice/text_to_speech.py` | OM Speech Generation Layer Future: - Coqui TTS - Piper - ElevenLabs |
| `om_ai/voice/voice_agent.py` | OM Voice Intelligence Agent |
| `om_ai/voice/voice_command.py` | OM Voice Command Analyzer |

### `om_ai/workflow/` — Workflow planner / executor

**8 Python files**

| Path | Role |
|------|------|
| `om_ai/workflow/__init__.py` |   init   |
| `om_ai/workflow/executor.py` | OM Workflow Execution Engine Responsible for: - Dynamic agent allocation - Agent execution - QA validation - Failure rec |
| `om_ai/workflow/generator.py` | OM Workflow Generation Engine Converts goals into executable workflows. |
| `om_ai/workflow/planner.py` | OM Dynamic Workflow Planner |
| `om_ai/workflow/recovery.py` | OM Workflow Failure Recovery |
| `om_ai/workflow/task.py` | OM Workflow Task |
| `om_ai/workflow/tracker.py` | OM Workflow Progress Tracker |
| `om_ai/workflow/workflow.py` | OM Workflow Model Represents a complete autonomous process. |

### `om_ai/workflow_memory/` — Workflow memory learning

**6 Python files**

| Path | Role |
|------|------|
| `om_ai/workflow_memory/__init__.py` |   init   |
| `om_ai/workflow_memory/extractor.py` | OM Workflow Pattern Extractor |
| `om_ai/workflow_memory/learner.py` | OM Autonomous Workflow Learning Engine |
| `om_ai/workflow_memory/matcher.py` | OM Workflow Similarity Matcher |
| `om_ai/workflow_memory/memory.py` | OM Workflow Experience Memory |
| `om_ai/workflow_memory/strategy.py` | OM Workflow Strategy Model |


---

## 15. Tests, scripts, docs index

### Tests
- `tests/` — primary pytest suite (`pyproject.toml` → `testpaths = ["tests"]`)
- `tests/distillation/` — distillation STEP tests
- Many root-level `test_*.py` smoke scripts (legacy / quick checks)

### Scripts (`scripts/`)
Train helpers, corpus packers, Mac→server 70B handoff (`pack_for_70b_server.sh`, `train_om1_mac_native.sh`, etc.).

### Docs (`docs/`) — start here for depth

| Doc | Topic |
|-----|-------|
| `QUICK_START.md` | Getting started |
| `ARCHITECTURE.md` / `CURRENT_ARCHITECTURE.md` | Architecture |
| `TRAINING.md`, `TRAINING_1B.md` … `TRAINING_70B.md` | Training scale |
| `SFT.md`, `DPO.md`, `RLHF.md` | Alignment |
| `AGENTS.md`, `MEMORY.md`, `RAG.md` | Runtime features |
| `SECURITY.md`, `DEPLOYMENT.md` | Ops |
| `OMAI_CORPUS_V1.md` | Corpus governance |
| `CONTINUOUS_LEARNING.md` | Feedback loops |
| `OM_FOUNDATION_UPGRADE_V1.md`, `OM_COMPLETION_ROADMAP.md` | Roadmaps |
| `JARVIS_OPERATING_INTELLIGENCE.md` | OI vision |
| `IMPLEMENTATION_STATUS.md` | Status honesty |

---

## 16. Honesty / boundaries

1. **This repo is working software** (code, trainers, API, UI). It is **not** a download of frontier OM-70B brains.  
2. `configs/*.json` define **shapes**, not trained intelligence.  
3. Useful skill requires **licensed data + real training** → checkpoints under `artifacts/checkpoints/`.  
4. OpenRouter / GPT / Claude give **API outputs**, not their private training sets or weights.  
5. Distill only from **allowed / distillable** models.  
6. Missing `OM_MODEL_CHECKPOINT` with `om_native` → **HTTP 503**, no silent third-party fallback.

---

## Quick production checklist

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env   # set checkpoint, tokenizer, keys
om-ai serve --host 127.0.0.1 --port 8080
# UI: http://127.0.0.1:8080/chat
# API docs: http://127.0.0.1:8080/docs
```

Optional OpenRouter improve loop:

```bash
# enable openrouter in Settings or env OPENROUTER_API_KEY
python -m om_ai.tools.llm_harvest --teachers openrouter --task "..." --out data/om_distillation/ --no-mock
om-ai sft ...   # train on exported JSONL
```

---

*End of PROJECT.md — full structure, flows, APIs, and file inventory for OM AI Operating Brain v0.3.*
