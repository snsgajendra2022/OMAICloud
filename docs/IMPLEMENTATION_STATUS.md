# Implementation Status — OM AI v0.3

## Software complete (executable in-repo)

Platform version target: **0.3.0** (`pyproject.toml`, FastAPI `om_ai/api/main.py`).

- Decoder-only Transformer (`om_ai/model/`): GQA/MHA, causal attention, optional cross-attention, RoPE, SwiGLU, RMSNorm/LayerNorm, residuals, KV cache, gradient checkpointing hooks
- Byte-level BPE tokenizer (`om_ai/tokenizer/`)
- License-first corpus path (`om_ai/data/`, `om_ai/corpus/`): manifest validation, PII scrub, exact/near-dup, audit, shard, stats CLI
- Pretrain trainer; DDP/FSDP (`distributed.py`); DeepSpeed ZeRO-3 entry
- Masked SFT; pairwise reward model; DPO; PPO infrastructure (GAE, clipped surrogate, KL)
- Checkpoint bundles with integrity; model registry lifecycle
- Benchmark runner + smoke/perplexity harness (`om_ai/eval/`)
- Feedback store + SFT/preference replay (`om_ai/continuous/`)
- SQLite multi-kind memory; persistent RAG; planner + agent orchestrator
- OpenAPI/project discovery; shell allow-list; knowledge tool; integration plugin SDK; HTTP connector; WhatsApp transport contract
- Trainable ViT + multimodal projector; speech STFT encoder + CTC head; multimodal request router
- Security: API keys, RBAC, SSRF guard, audit log, rate limits, secret store (`om_ai/security/`)
- FastAPI v0.3 surface + CLI (`om-ai …`)
- Docker / compose packaging
- Tiny demo DPO checkpoint proving pretrain→SFT→DPO trains real tensors
- Automated tests under `tests/` (run `pytest -q`)

## Requires external training / providers (not claimed done)

- Frontier-quality **trained** 1B / 7B / 13B / 70B weights
- Billions–trillions of licensed training tokens
- Large GPU cluster wall-time for those scales
- Large curated instruction and preference corpora
- Production VLM / ASR / TTS weights and datasets (TTS is contract-only here)
- Per-product integration credentials and compliance
- Production WhatsApp transport/session

## v0.3 vs training reality

| Layer | Status |
|-------|--------|
| Software platform (code, CLI, API, trainers, agents, RAG, security) | **Complete for v0.3 software scope** |
| Tiny pipeline demo weights | Present under `artifacts/demo/` — not a capable LM |
| OM-1B / 7B / 13B / 70B intelligence | **Not complete** until real data + compute produce and pass evals |

A neural network’s learned knowledge is in its weights. Source code implements learning mechanisms; it does not substitute for data, optimization runs, and resulting parameters. See `TRAINING_RUNBOOK.md`, `EXTERNAL_ASSETS_REQUIRED.md`, and `TRAINING_70B.md`.
