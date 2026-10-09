# OM AI: Phase 1–200 implementation and certification status

This is an evidence-driven engineering register, not a claim that all 200 phases are implemented. The machine-readable starter registry is `configs/om_capability_registry.json`; the runner is `scripts/certify_om.py`.

## First implementation increment (this commit series)

| Work | Implementation | Evidence status |
|---|---|---|
| Request/trace IDs and request lifecycle | `om_ai/runtime/observability.py` | Implemented in source; local tests not run by GitHub connector |
| Pipeline entrypoint tracing | `@trace_function("chat.pipeline")` on `run_chat_pipeline` | Wired at source level; end-to-end trace not yet verified |
| Privacy guard for telemetry | Only allowlisted scalar attributes; no prompts/outputs recorded | Unit tests added; must run locally |
| Capability registry | `configs/om_capability_registry.json` | Initial critical-path inventory; deliberately incomplete |
| Certification runner | `scripts/certify_om.py` | Compile/audit by default; optional full tests and native evaluation |
| Existing architecture scanner | `scripts/audit_om_architecture.py` | Must be run on the target checkout |

## Required local verification

Run from the repository root and the intended branch:

```bash
python -m compileall -q om_ai scripts
python -m pytest tests/test_observability.py tests/test_observability_decorator.py -q
python scripts/certify_om.py --run-tests
python scripts/certify_om.py --run-model-eval
```

The native model evaluation needs the actual local checkpoint and tokenizer configured in the developer's ignored local environment. Never commit `.env`, API keys, private data, or model weights as a shortcut.

## Execution order

1. **P0: Model correctness** — establish the actual checkpoint, canonical tokenizer, vocabulary/config compatibility, generation quality, and a single authoritative gateway. Earlier local evidence was 0/13 capability checks; that is a release blocker until rerun.
2. **P1: Runtime certification** — trace actual API → conversation → context/memory/RAG → gateway → model → quality gate; remove duplicate or unreachable generation paths only after the audit maps them.
3. **P2: Data/training** — reproducible licensed data pipeline, pretraining, SFT, preference training, checkpoints/resume, and fixed evaluation splits.
4. **P3: Security/reliability** — tenant isolation, permissions, audit logs, failure semantics, regression and red-team tests.
5. **P4: Scaling/research** — distributed training/serving, MoE, long context, multimodal and autonomous learning only when baseline measurements justify them.

## Status semantics

- `IMPLEMENTED`: source exists.
- `CONNECTED`: a verified production call path reaches it.
- `EXECUTED`: a runtime execution record exists.
- `TESTED`: relevant automated tests passed.
- `BENCHMARKED`: versioned benchmark results exist.
- `PRODUCTION`: deployed and observed under production conditions.
- `CERTIFIED`: all required evidence and dependencies pass.

A capability cannot be marked certified just because a file exists or a compile command succeeds. A native model that produces incoherent text is not certified, even if its checkpoint loads and a forward pass runs. Frontier-level capability can only be claimed from fair, repeatable benchmark evidence.
