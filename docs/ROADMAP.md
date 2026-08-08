# OM AI Production Roadmap

## Phase 1 — Foundation model engineering

1. Build legally sourced corpus ingestion connectors.
2. Train tokenizer on representative multilingual/code/business data.
3. Establish tiny/125M/1B scaling experiments.
4. Track training loss, validation loss, throughput, GPU utilization and data provenance.
5. Add instruction tuning and preference/alignment datasets.
6. Add robust benchmark suites and model cards.

## Phase 2 — Cognitive services

- Semantic embedding model trained/hosted locally.
- Vector database abstraction.
- Episodic, semantic and procedural memory policies.
- Structured planner trained to emit validated tool calls.
- Critic/verifier model for reflection and outcome checking.
- Sandboxed code execution service.

## Phase 3 — Multimodal + action

- Local VLM backend for image/screenshot/document understanding.
- OCR/document layout encoder.
- Local ASR and TTS backends.
- Browser automation worker with explicit policy boundaries.
- API schema discovery, auth vault and action approvals.
- WhatsApp/CRM/medical/e-commerce adapters.

## Phase 4 — Enterprise platform

- Tenant isolation and RBAC.
- Secrets vault integration.
- SSO/OIDC.
- Audit/event ledger.
- Tool-level authorization and approval workflows.
- Data retention/deletion policies.
- Observability with metrics/traces/logs.
- Kubernetes operators and GPU inference serving.

## Phase 5 — Large-scale training

For 7B/13B/70B+ training, add:

- Tensor parallelism and sequence parallelism (Megatron-style or equivalent).
- Checkpoint sharding and elastic recovery.
- Object storage for datasets/checkpoints.
- High-throughput streaming dataset loader.
- Network topology-aware scheduling.
- NCCL monitoring.
- Loss spike detection and bad-batch quarantine.
- Continuous evaluation gates.
