# OM AI Operating Brain v0.3

Self-hosted, API-independent AI platform foundation: train and run your own models, agents, memory, and RAG without calling OpenAI, Anthropic, or Google model APIs.

## Honesty about weights

This repository is **working software** (architecture, trainers, agents, API). It is **not** a download of trained OM-1B / 7B / 13B / 70B brains.

- Architecture presets under `configs/` describe model **shapes**
- Useful intelligence requires licensed data + real GPU training that produce checkpoint files
- Included `artifacts/demo/om-tiny-dpo.pt` proves the training pipeline runs end-to-end on toy data — it is not frontier capability
- No fabricated benchmark leaderboard scores are claimed

See `docs/IMPLEMENTATION_STATUS.md` and `docs/EXTERNAL_ASSETS_REQUIRED.md`.

## Quick start (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

om-ai tokenizer train --input data/example_corpus.txt --output artifacts/tokenizer.json --vocab-size 512
om-ai train --config configs/tiny.json --data data/example_corpus.txt --tokenizer artifacts/tokenizer.json --steps 20
om-ai generate --config configs/tiny.json --tokenizer artifacts/tokenizer.json --checkpoint artifacts/checkpoints/latest.pt --prompt "OM AI"

om-ai serve --host 127.0.0.1 --port 8080
# Chat UI: http://127.0.0.1:8080/ui/chat  (same as /ui/tokens)
# Coherent English: start Ollama (`ollama serve` + `ollama pull llama3.2`) or set
# OPENAI_API_KEY / OM_AI_OPENAI_API_KEY. Tiny local demo weights are not smart.
```

One-shot tiny pipeline: `python scripts/run_actual_training_pipeline.py --steps 5`

**OM-70B:** Mac prepares corpus/tokenizer/configs; final train is on a CUDA+DeepSpeed server — see [`docs/SERVER_70B_HANDOFF.md`](docs/SERVER_70B_HANDOFF.md). Pack upload set: `./scripts/pack_for_70b_server.sh`.

## Major CLI commands

| Command | Purpose |
|---------|---------|
| `om-ai model-info` | Parameter estimate from config |
| `om-ai tokenizer train\|inspect\|encode\|decode` | Byte-BPE tokenizer |
| `om-ai corpus import\|validate\|dedupe\|audit\|shard\|stats` | Corpus governance |
| `om-ai pretrain` / `om-ai train` | Causal pretraining |
| `om-ai sft` / `om-ai reward` / `om-ai dpo` | Post-training |
| `om-ai evaluate` / `om-ai benchmark` | Local eval harness |
| `om-ai generate` / `om-ai chat` | Inference |
| `om-ai feedback add\|export` | Continuous-learning I/O |
| `om-ai registry list\|register` | Model lifecycle registry |
| `om-ai bundle` | Checkpoint bundle + integrity |
| `om-ai project-scan` | Local project discovery |
| `om-ai serve` | FastAPI server |

## What v0.3 includes

- From-scratch decoder-only Transformer (RoPE, GQA/MHA, SwiGLU, KV cache, optional cross-attention)
- Custom byte-level BPE; corpus governance and sharding
## Training at scale

- Tiny / single GPU: `om-ai train ...`
- OM-70B launcher (GPU cluster): `om-ai train-70b --data ... --tokenizer ... --output ...`
- Mac → server handoff: `docs/SERVER_70B_HANDOFF.md` (also `docs/TRAINING_70B.md`). `serve` never starts 70B training.

- Single-process training; DDP/FSDP; optional DeepSpeed
- SFT, reward model, DPO, PPO infrastructure
- Agents, SQLite memory, local RAG, security (API keys, RBAC, SSRF, audit, rate limits)
- Vision / speech training foundations + multimodal router
- Integrations plugin SDK, Docker, tests

## Docs index

Start with `docs/QUICK_START.md`, `docs/ARCHITECTURE.md`, `docs/TRAINING.md`. Scale-specific: `TRAINING_1B.md` … `TRAINING_70B.md`. Alignment: `SFT.md`, `DPO.md`, `RLHF.md`. Runtime: `AGENTS.md`, `MEMORY.md`, `RAG.md`, `DEPLOYMENT.md`, `SECURITY.md`.

## Requirements

Python ≥ 3.11, PyTorch ≥ 2.4. Linux + CUDA for serious distributed training.

## Frontier-model reality

Owning a capable private model still means: licensed corpus → tokenizer → cluster pretrain → SFT/alignment → eval → deployed weights. This repo is the engineering foundation for that process — not a substitute for the training work itself.
