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

## Self-hosted vLLM production path (2026-10)

The configured target architecture now has a separate vLLM adapter:

- `OM_MODEL_PROVIDER=vllm` / `OM_AI_CHAT_BACKEND=vllm` selects a self-hosted OpenAI-compatible inference server.
- `OM_VLLM_BASE_URL`, `OM_VLLM_MODEL`, and optional `OM_VLLM_API_KEY` configure the endpoint.
- The OpenAI-compatible OM API routes chat to that adapter and maps vLLM connection/model errors to HTTP 503.
- Added `docker-compose.vllm.yml` for a private-network NVIDIA GPU deployment, plus tests for routing, endpoint payloads, and fail-closed behavior.
- `.env.example` now documents vLLM as the production target and leaves the native OM checkpoint as an optional diagnostic/research path.

This is implementation of the serving path—not proof of GPT-5-level capability. No selected model weights, deployment GPU, real inference benchmark, or GPT-5 comparison was supplied or run. Model selection, license review, actual deployment, quality benchmarks, security tests, and load tests remain release gates. See `docs/SELF_HOSTED_LLM_RUNTIME.md`.

## Pretrained provider and dataset/hardware utilities (2026-10)

The following software changes are now on the feature branch:

- Added an optional Transformers inference adapter in `om_ai/backends/transformers_backend.py`. It loads the selected model's own tokenizer, requires its chat template, reports the actual loaded parameter count, supports ordinary generation and streamer-based output, and can request device-map placement plus optional bitsandbytes 4-bit/8-bit loading on supported systems.
- Added explicit `OM_MODEL_PROVIDER=transformers` / `OM_AI_CHAT_BACKEND=transformers` routing to the existing chat layer. This path does not silently fall back to the native OM checkpoint or inject OM-1.0 identity into the selected pretrained model's system context.
- Added optional `hf` and `hf-quant` dependency groups. The default install remains native OM and does not download model weights.
- Added `scripts/estimate_llm_memory.py` for transparent weight/KV-cache planning estimates.
- Added `scripts/validate_chat_dataset.py` for JSONL/JSON/text and optional Parquet schema checks, source SHA-256, exact duplicates, and exact train/eval overlap.
- Added focused tests for provider selection/fail-closed behavior and data/memory utilities.
- Added `docs/PRETRAINED_MODEL_RUNTIME.md` and environment examples.

### Acceptance status for the new path

| Area | Status |
|---|---|
| Code committed to feature branch | Implemented |
| Optional dependencies / no default model download | Implemented |
| Explicit provider selection and no silent fallback | Implemented in code; CI result pending |
| Pretrained tokenizer/chat-template use | Implemented; requires validation against the actual chosen model |
| 4-bit/8-bit quantization | Implemented as an optional supported-platform path; hardware-dependent |
| Memory estimator and dataset manifest validator | Implemented; CI result pending |
| Real 70B weights downloaded and loaded | Not done; no model artifact or target hardware was supplied |
| 70B training from scratch | Not done; requires licensed large-scale corpus and distributed GPU infrastructure |
| Production load/concurrency/cancellation tests | Not done; runtime and deployment hardware required |
| Native OM capability quality | Still limited by the existing small checkpoint and must be evaluated separately |

A green unit-test workflow will validate code paths only; it does not prove that a large model fits, that a licensed model is available, or that 70B inference is production-ready. Model download/load tests, actual latency/memory benchmarks, license review, and full API/security/load testing remain required before production deployment.

