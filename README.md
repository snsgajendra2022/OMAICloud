# OM AI Operating Brain v0.3

Self-hosted, API-independent AI platform: train and run **OM-1.0** natively — no Ollama, Llama proxy, or third-party LLM required for the default serve path.

**Full structure + production blueprint:** [`docs/PROJECT_BLUEPRINT.md`](docs/PROJECT_BLUEPRINT.md)

**Companion (13-layer):** understanding → emotion → memory → dialogue → reasoning → knowledge (RAG) → research (no auto-redirect) → permission → brother personality → voice/avatar → self-learning. Entry: `om_ai.core.companion_architecture`.

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

## Frontier-model reality

Owning a capable private model still means: licensed corpus → tokenizer → cluster pretrain → SFT/alignment → eval → deployed weights. This repo is the engineering foundation for that process — not a substitute for the training work itself.
