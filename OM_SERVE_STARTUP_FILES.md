# OM AI — Start Project (`om-ai serve`) File Map

Use this when you start the app with:

```bash
om-ai serve --host 127.0.0.1 --port 8080
```

UI after start:

| URL | Page |
|-----|------|
| http://127.0.0.1:8080/ | redirects → `/login` |
| http://127.0.0.1:8080/login | login |
| http://127.0.0.1:8080/chat | chat UI (after sign-in) |

---

## 1. Startup call chain (what runs first)

```
pyproject.toml  [project.scripts]
  om-ai = om_ai.cli:main
        │
        ▼
om_ai/cli.py
  main() → serve(args)
    load_dotenv()                 ← om_ai/env.py  (+ repo .env)
    uvicorn.run("om_ai.api.main:app", host, port)
        │
        ▼
om_ai/api/main.py                 ← FastAPI app created + routers wired
  native checkpoint autoload
  READY / NOT READY banner
  Uvicorn listening on 127.0.0.1:8080
```

### Entry / config files

| Role | Path |
|------|------|
| CLI entry script | `pyproject.toml` → `[project.scripts] om-ai` |
| CLI `serve` command | `om_ai/cli.py` (`serve()`, parser around `--host` / `--port`) |
| Env loader | `om_ai/env.py` |
| Local env values | `.env` (repo root) |
| FastAPI application | `om_ai/api/main.py` |

---

## 2. Files loaded when `main.py` imports (server boot)

These run **once** at process start (before the first HTTP request).

### Core app + API routers

| File | Role |
|------|------|
| `om_ai/api/main.py` | App factory, singletons, autoload, UI routes |
| `om_ai/api/deps.py` | Auth dependencies |
| `om_ai/api/openai_compat.py` | OpenAI-compatible `/api/v1/chat/completions` |
| `om_ai/api/conversations.py` | Conversations API |
| `om_ai/api/auth_routes.py` | Login / register / session |
| `om_ai/api/workspace_routes.py` | Projects / workspace |
| `om_ai/api/oi_routes.py` | Operating-intelligence routes |
| `om_ai/api/platform_routes.py` | Platform settings |
| `om_ai/api/foundation_routes.py` | Foundation routes |

### Runtime + model backend

| File | Role |
|------|------|
| `om_ai/runtime/engine.py` | `LocalLLMEngine` (weights + generate) |
| `om_ai/runtime/chat_backend.py` | `chat_reply()` — brain + native chat |
| `om_ai/backends/om_native.py` | `OMNativeBackend`, `default_native_paths()` |
| `om_ai/backends/om_registry.py` | OM-1.0 registry sync |
| `om_ai/backends/base.py` | `NativeCheckpointError` |
| `om_ai/tokenizer/loader.py` | Loads HF / ByteBPE tokenizer |
| `om_ai/model/` (+ config) | Transformer architecture for OM-1.0 |

### Security / memory / knowledge (boot singletons)

| File | Role |
|------|------|
| `om_ai/security/auth.py` | API keys + session auth |
| `om_ai/security/audit.py` | SQLite `AuditLog` |
| `om_ai/security/rate_limit.py` | Rate limiter |
| `om_ai/security/ssrf.py` | SSRF guard |
| `om_ai/security/tokens.py` | Named API tokens DB |
| `om_ai/security/accounts.py` | Accounts / register |
| `om_ai/memory/` (SQLite store) | Chat / long memory DB wiring |
| `om_ai/knowledge/` | Persistent knowledge base |
| `om_ai/registry/` | Model registry under `artifacts/registry` |
| `om_ai/agents/orchestrator.py` | Tool-capable agent orchestrator |
| `om_ai/actions/` | Shell + knowledge tools |
| `om_ai/continuous/feedback.py` | Feedback store |

### Static UI served by FastAPI

| URL | File |
|-----|------|
| `/login` | `om_ai/api/static/login.html` |
| `/register` | `om_ai/api/static/register.html` |
| `/chat` | `om_ai/api/static/chat.html` |
| `/tokens` | `om_ai/api/static/tokens.html` |

---

## 3. Model / data paths used at boot (from `.env`)

| Env key | Typical path | Used by |
|---------|--------------|---------|
| `OM_MODEL_CHECKPOINT` / `OM_AI_CHECKPOINT` | `artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt` | Native load |
| `OM_MODEL_TOKENIZER` / `OM_AI_TOKENIZER` | `artifacts/tokenizer-production-65536.json` | Tokenizer |
| `OM_MODEL_CONFIG` / `OM_AI_CONFIG` | `configs/om-1.0-local.json` | Model config |
| `OM_AI_DB` | `artifacts/om_ai.sqlite3` | Memory + conversations |
| `OM_AI_KB` | `artifacts/knowledge.sqlite3` | Knowledge base |
| `OM_AI_AUDIT_DB` | `artifacts/audit.sqlite3` (or similar) | Audit log |
| `OM_AI_TOKENS_DB` | `artifacts/tokens.sqlite3` | API tokens |
| `OM_AI_ACCOUNTS_DB` | `artifacts/accounts.sqlite3` | User accounts |
| `OM_AI_REGISTRY` | `artifacts/registry` | Model registry |
| `OM_AI_FEEDBACK_DB` | `artifacts/feedback.sqlite3` | Feedback |

Related optional symlink / model metadata:

- `artifacts/models/om-1.0/checkpoint.pt`
- `artifacts/models/om-1.0/metadata.json`

---

## 4. What runs when you chat (request path)

Browser (`chat.html`) →:

```
POST /api/v1/chat/completions
  om_ai/api/openai_compat.py
    → chat_reply()
      om_ai/runtime/chat_backend.py
        → cognitive brain / Absolute OS (when enabled)
          om_ai/core/cognitive/brain_pipeline.py
          om_ai/core/reasoning/pipeline.py
          om_ai/core/response/response_formatter.py
        → optional native generate
          om_ai/backends/om_native.py
          om_ai/runtime/engine.py
```

### Chat-related modules

| Path | Role |
|------|------|
| `om_ai/api/static/chat.html` | UI; streams completions |
| `om_ai/api/openai_compat.py` | OpenAI-compatible endpoint |
| `om_ai/runtime/chat_backend.py` | Backend selection + reply |
| `om_ai/runtime/chat_orchestrator.py` | Orchestration helpers |
| `om_ai/core/cognitive/brain_pipeline.py` | `OMCognitiveBrain` |
| `om_ai/core/reasoning/pipeline.py` | Reasoning pipeline |
| `om_ai/core/reasoning/reasoning_chain.py` | Reasoning chain |
| `om_ai/core/response/response_formatter.py` | User vs developer reply |
| `om_ai/core/response/answer_generator.py` | Answer generation |
| `om_ai/understanding/query_kind.py` | Greeting / knowledge / coding |
| `om_ai/cognition/intent_engine.py` | Intent |
| `om_ai/cognition/task_planner.py` | Task plan |
| `om_ai/cognition/technology_engine.py` | Tech stack detect |
| `om_ai/agents/router.py` | Agent routing |
| `om_ai/agents/executor.py` | Agent execute |
| `om_ai/agents/collaboration/` | Multi-agent plan/coord |
| `om_ai/orchestration/orchestrator.py` | OM orchestrator |
| `om_ai/knowledge/facts.py` | Built-in facts |
| `om_ai/knowledge/context_filter.py` | Knowledge hit filter |

Auth for chat UI / API:

| Path | Role |
|------|------|
| `om_ai/api/auth_routes.py` | `/v1/auth/*` |
| `om_ai/security/session_cookie.py` | Cookie session |
| `om_ai/api/deps.py` | `require_auth` / permissions |

---

## 5. Quick “start checklist” file list

Minimum files/paths involved when you run `om-ai serve`:

1. `pyproject.toml`
2. `om_ai/cli.py`
3. `om_ai/env.py`
4. `.env`
5. `om_ai/api/main.py`
6. `om_ai/api/openai_compat.py`
7. `om_ai/backends/om_native.py`
8. `om_ai/runtime/engine.py`
9. `om_ai/runtime/chat_backend.py`
10. `configs/om-1.0-local.json`
11. `artifacts/tokenizer-production-65536.json`
12. `artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt`
13. `om_ai/api/static/login.html`
14. `om_ai/api/static/chat.html`

---

## 6. Restart note

After code or dependency changes (for example installing `tokenizers`), stop the old process and start again:

```bash
om-ai serve --host 127.0.0.1 --port 8080
```

Expect the native banner in the terminal (`Status: READY`) before chatting at http://127.0.0.1:8080/chat.

## 7. Ops commands (diagnostics)

| Command | File |
|---------|------|
| `om-ai doctor` | `om_ai/diagnostics/system_check.py` |
| `om-ai status` | `om_ai/cli.py` → status_cmd |
| `om-ai repair` | `om_ai/diagnostics/repair.py` |
| Checkpoint check | `om_ai/backends/checkpoint_checker.py` |
| Health API | `GET /health` in `om_ai/api/main.py` |
| Logs | `logs/application.log`, `logs/error.log`, `logs/security.log` |

See also: `OM_AI_SYSTEM_STATUS.md`
