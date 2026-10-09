# OM AI Operating Brain v0.3

Self-hosted, API-independent AI platform: train and run **OM-1.0** natively — no Ollama, Llama proxy, or third-party LLM required for the default serve path.

**Full structure + production blueprint:** [`docs/PROJECT_BLUEPRINT.md`](docs/PROJECT_BLUEPRINT.md)
**Native capability/parity upgrade plan:** [`docs/OM_NATIVE_CAPABILITY_ROADMAP.md`](docs/OM_NATIVE_CAPABILITY_ROADMAP.md)

**Companion (13-layer):** understanding → emotion → memory → dialogue → reasoning → knowledge (RAG) → research (no auto-redirect) → permission → brother personality → voice/avatar → self-learning. Entry: `om_ai.core.companion_architecture`.

The `data/models/om_registry.json` file is descriptive metadata, not a weight store. Entries without a real checkpoint path, checksum, tokenizer binding, and evaluation results are marked unverified and must not be presented as installed models. Local files under `artifacts/` are intentionally git-ignored, so GitHub alone cannot confirm whether your machine has those weights.

## Honesty about weights

This repository is **working software** (architecture, trainers, agents, API). It is **not** a download of trained OM-1B / 7B / 13B / 70B brains.

- Architecture presets under `configs/` describe model **shapes**
- Useful intelligence requires licensed data + real GPU training that produce checkpoint files
- Local OM-1.0 smoke/long/chat checkpoints prove the native pipeline; they are **not** frontier capability
- No fabricated benchmark leaderboard scores are claimed

See `docs/PROJECT_BLUEPRINT.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/EXTERNAL_ASSETS_REQUIRED.md`, and the docs index below.

## Quick start (OM-1.0 native)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,companion]'

# Configure checkpoint + device in .env (see .env.example)
om-ai model-info

# Native companion window (system UI — not a browser tab)
om-ai start
# or:  om-ai companion desktop

# API-only server (optional)
om-ai serve --host 127.0.0.1 --port 8080
# Browser fallback:  om-ai start --browser
```

OM Companion desktop stays **always on top**, hides to the **menu bar** when you close the window, and keeps running while you switch apps/screens.

Default env (see `.env.example`):

- `OM_MODEL_PROVIDER=om_native`
- `OM_MODEL_CHECKPOINT=artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt` (or long/smoke if present)
- `OM_MODEL_DEVICE=mps` only when MPS is available; otherwise `cpu` / `cuda`
- Missing / unloadable checkpoint → clear error / grounded fallbacks — **no** third-party LLM fallback by default

Optional short smoke train:

```bash
om-ai train-om1 --config configs/om-1.0-local.json --steps 20
```

## Major CLI commands

| Command | Purpose |
|---------|---------|
| `om-ai model-info` | OM-1.0 native info |
| `om-ai train-om1` | Local OM-1.0 smoke / continue training |
| `om-ai tokenizer train\|inspect\|encode\|decode` | Byte-BPE tokenizer |
| `om-ai corpus …` | Corpus governance |
| `om-ai pretrain` / `train` / `sft` / `dpo` | Training stack |
| `om-ai generate` / `om-ai chat` | Inference |
| `om-ai serve` | FastAPI server (OM native by default) |

## What v0.3 includes

- From-scratch decoder-only Transformer (RoPE, GQA/MHA, SwiGLU, KV cache)
- Custom byte-level BPE; corpus governance
- OM-1.0 native backend + registry
- Chat intelligence + companion / Jarvis runtime
- Agents, SQLite memory, local RAG, security
- Vision / speech foundations + multimodal router

## Docs index

| Doc | Topic |
|-----|--------|
| **[PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md)** | **Full structure + production runtime map** |
| [QUICK_START.md](docs/QUICK_START.md) | Getting started |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layer overview |
| [CURRENT_ARCHITECTURE.md](docs/CURRENT_ARCHITECTURE.md) | Hot-path runtime |
| [COMPANION_PAGE.md](docs/COMPANION_PAGE.md) | Companion UI |
| [TRAINING.md](docs/TRAINING.md) | Training |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deploy |

## Requirements

Python ≥ 3.11, PyTorch ≥ 2.4. Linux + CUDA for serious distributed training; Apple Silicon can use `mps` when available.

## Controlled ML lifecycle and Learning Lab

The chat workspace includes a **Learning Lab** for tenant-scoped feedback, dataset validation/versioning, and explicit smoke evaluation through the canonical ModelGateway.

- `GET /api/ml/status` reports learning configuration, recent dataset manifests, feedback count, registered checkpoint metadata, and the configured model id. It does not load or modify weights.
- `POST /api/ml/feedback` records feedback as a candidate signal. `consent_to_training` defaults to `false`; feedback collection never starts training.
- `POST /api/ml/datasets/prepare` validates examples containing non-empty `question` and `answer`, writes a content-addressed JSONL dataset and manifest, and reports deterministic train/validation/test split counts. Requires admin permission.
- `POST /api/ml/datasets/from-feedback` builds a dataset only from positive feedback with explicit training consent. Rejected answers are not mislabeled as SFT targets. Requires admin permission.
- `POST /api/ml/evaluate` explicitly runs smoke questions through ModelGateway and reports non-empty and echo rates. Requires admin permission and a usable configured model.

The initial learning foundation is intentionally **safe-by-default**:

- `OM_LEARNING_ENABLED=false` by default. When enabled, training still requires an explicit training adapter.
- `OM_LEARNING_AUTO_PROMOTION=false` by default. Candidate checkpoints must be evaluated and approved before production promotion.
- Dataset and feedback files are stored under a tenant-specific hashed directory beneath `OM_LEARNING_ROOT` (default `artifacts/learning`).
- OM-L1 through OM-L5 in the chat picker are behavior/evolution profiles unless the model catalog and registry confirm real, compatible checkpoints. A label is not proof that a separate trained model is installed.

The existing training stack (pretraining, SFT, DPO/PPO, reward modeling, and registry components) remains the training implementation source. The Learning Lab does not claim to implement every algorithm simply because a UI control exists, and it never promotes new weights automatically.

## Frontier-model reality

Owning a capable private model still means: licensed corpus → tokenizer → cluster pretrain → SFT/alignment → eval → deployed weights. This repo is the engineering foundation for that process — not a substitute for the training work itself.


## Context-aware conversation pipeline

The production `chat_reply` path now runs `om_ai.core.conversation.ConversationEngine` before the existing generation cascade. It classifies the relationship of a turn to recent history, resolves pronoun/reference candidates against actual prior turns, ranks relevant history, and injects a bounded context note while preserving the current user message and system instructions. It does not generate answers or replace the configured model.

Configure with `OM_CONVERSATION_CONTEXT=1` (default), `OM_CONVERSATION_MAX_HISTORY=8`, `OM_CONVERSATION_MAX_RELEVANT=4`, and `OM_CONVERSATION_SUMMARY_MAX_CHARS=700`. Set the first variable to `0` only for diagnostics. This is a lightweight lexical/recency ranker, not an embedding-based semantic search system; a production semantic retriever can later be plugged into the same context layer.


## Native dynamic chat (no external LLM)

Keep `OM_MODEL_PROVIDER=om_native` and `OM_AI_CHAT_BACKEND=om_native`. Set `OM_NATIVE_MODEL_FIRST=1` so the native OM checkpoint generates the final chat answer instead of deterministic greeting/identity shortcuts. This setting does not create model capability by itself: the intended trained checkpoint must exist, load successfully, and match the tokenizer.

Verify locally with:

```bash
pytest -q tests/test_chat_backend.py
om-ai model-info
om-ai serve --host 127.0.0.1 --port 8080
```

Then test multiple distinct questions and follow-ups against `POST /v1/chat` and inspect server logs/metadata to confirm native generation is actually used. Keep provider credentials out of the React client. Response quality still depends on checkpoint weights, tokenizer compatibility, training data, context length, and training compute.
