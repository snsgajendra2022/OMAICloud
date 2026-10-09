# OM 24-Phase Implementation Program

## Mission

Build OM as a self-owned model and AI product, with a single accountable generation path, reproducible training, model/data provenance, measured evaluation, and production operations. This is an execution program, not a claim that every phase is already complete or that OM matches a frontier cloud model.

## Execution rules

1. **One canonical generation contract.** Product surfaces call the OM runtime and ModelGateway; provider/model selection is explicit and observable.
2. **No fake success.** Readiness requires a real checkpoint, compatible architecture and tokenizer, a successful generation smoke test, and a passing quality gate.
3. **No silent answer substitution.** Templates may be UI copy only. They must never be labelled as model output. Tool/RAG results keep provenance and are passed to the model for synthesis when the native model is the selected generator.
4. **No unlicensed training data.** Dataset manifests record source, license/permission, collection date, transformations, and exclusions. User conversations are not training data without explicit consent and privacy controls.
5. **No invented benchmark claims.** Report dataset/version, scoring rules, model/checkpoint hash, hardware, runtime settings, raw outputs, and uncertainty.
6. **Every phase has a gate.** Work advances by tested increments; a phase is not marked complete merely because files exist.
7. **Local assets are not assumed to be in Git.** The tokenizer/checkpoint on the developer's machine must be audited and hashed locally; never commit private keys, .env secrets, or large weights without an explicit artifact policy.

## Baseline facts known from repository inspection

- The README says architecture/trainer code is present but production-scale OM weights are not shipped; local artifacts are git-ignored.
- `configs/om-1.0-local.json` specifies a 65,536-token vocabulary, 4 layers, width 256, context 256, and a roughly 20M-parameter target.
- The native runtime has checkpoint/tokenizer loading and vocabulary compatibility checks.
- The repository contains tokenizer, Transformer, pretraining, SFT, reward/DPO/PPO infrastructure, evaluation, registry, memory, RAG, agents, API, and multimodal modules. Presence of code does not prove end-to-end correctness.
- Previously shared local evaluation: 0/13 capability smoke cases and incoherent native generations. This remains a release blocker until rerun against the exact checkpoint and fixed harness.
- Static GitHub inspection cannot inspect ignored local checkpoint bytes, local .env values, or reproduce Mac MPS execution. Those require local commands and sanitized reports.

## Phase register and acceptance gates

| Phase | Scope | Required completion evidence | Initial status |
|---|---|---|---|
| 01 | Repository / architecture audit | Generated file inventory, generation call-site map, tokenizer/checkpoint references, API/CLI entrypoint map, dependency-cycle report, runtime trace | In progress: audit script added; run it locally |
| 02 | Core runtime foundation | `compileall`, import smoke tests, no unintended import cycles, documented runtime ownership | Not verified |
| 03 | Tokenizer system | Round-trip/property tests; deterministic fingerprint; special-token tests; model/tokenizer vocab and checkpoint fingerprint match | Blocked on local checkpoint audit |
| 04 | Foundation architecture | Versioned config/schema, parameter count, architecture compatibility tests, context and precision documented | Partial code exists; tests needed |
| 05 | Dataset engineering | License-aware manifests, dedup/PII/safety audit, dataset versions and leakage-resistant splits | Code exists; corpus/data not audited here |
| 06 | Pretraining | Reproducible run, finite train/validation loss, optimizer-step test, checkpoint reload/resume, tokens/sec report | Not verified |
| 07 | SFT | Assistant-only loss tests, curated/licensed examples, held-out validation, regression report | Code exists; trained checkpoint quality unverified |
| 08 | Preference / RL | Chosen/rejected validation, reward/DPO tests, reward-hacking checks, offline evaluation before any online RL | Infrastructure exists; outcome unverified |
| 09 | Evaluation | Versioned tests across capabilities, raw outputs, deterministic checks, human review where needed | Harness exists; prior local result 0/13 |
| 10 | Checkpoint registry | Checksums, tokenizer/config binding, training metadata, state-transition tests, promotion gates | Registry code exists; production artifact binding unverified |
| 11 | ModelGateway | One contract for generate/stream/embed, explicit provider choice, provenance, timeouts and typed errors | Canonical gateway requires audit/implementation |
| 12 | Production inference | Load + compatibility + generation readiness, batching/cache/streaming/cancel tests, CPU/MPS/CUDA behavior | Native generation quality is currently a blocker |
| 13 | Conversation intelligence | Multi-turn relation/reference/task tests; no canned response path in model-owned mode | Components exist; end-to-end tests needed |
| 14 | Context / long-term memory | Tenant isolation, retention/deletion, retrieval relevance, bounded context, consent controls | Components exist; security/relevance tests needed |
| 15 | RAG / knowledge | Ingestion, chunking, retrieval/reranking, citations, freshness, source attribution, groundedness tests | Components exist; end-to-end evaluation needed |
| 16 | Reasoning / planning | Structured plan/execute/verify interfaces, tool result verification, no fake chain-of-thought | Partial components; tests needed |
| 17 | Agent / tools | Typed tool schemas, permissions, allow-list, validation, audit log, failure/retry policy | Components exist; end-to-end security tests needed |
| 18 | Multimodal | Per-modality capability declaration, encoder/model compatibility, evaluation datasets, honest unsupported-mode errors | Infrastructure exists; trained modality weights not verified |
| 19 | Quality / safety | Relevance/context/safety/garbage gates, bounded regeneration, explicit failure state, provenance | Recent native-first routing changes require local tests |
| 20 | Continuous learning | Consent-aware feedback, reviewed dataset promotion, reproducible offline training, rollback | Infrastructure exists; safe lifecycle unverified |
| 21 | Cloud infrastructure | Container deployment, auth, quotas, tracing/metrics, health/readiness, scaling/load test | Deployment code exists; production environment not verified |
| 22 | API / application platform | Contract tests for chat/stream/models/health/usage, auth and error schemas | API exists; endpoint inventory/test audit needed |
| 23 | Chat UX | Streaming, attachments, citations, tool states, errors, history, accessibility, backend-truthful status | Product surfaces exist; UX regression audit needed |
| 24 | Production operations / benchmark | Release gate, SLOs, rollback, incident runbooks, fixed benchmark and version-to-version comparison | Not verified |

## Dependency order

The phases are not a strictly linear list. The critical path for a trustworthy native assistant is:

1. Phase 01 audit and baseline capture.
2. Phases 02–04: runtime ownership, tokenizer/model/checkpoint compatibility.
3. Phases 05–08: data governance and training runs, only after the base pipeline is validated.
4. Phases 09–10: evaluation and registry promotion gates.
5. Phases 11–12: canonical gateway and production inference.
6. Phases 13–19: context, memory, RAG, reasoning, tools, multimodal and quality gates, all routed through the same gateway.
7. Phases 20–24: consent-controlled learning, deployment, API/UX hardening and release operations.

API, UI, data governance, and test infrastructure can progress in parallel, but a poor native checkpoint must not be promoted as production-ready.

## Phase 01: first local run

From the repository root:

```bash
source .venv/bin/activate
python scripts/audit_om_architecture.py
python -m compileall -q om_ai scripts
python -m pytest -q
python scripts/diagnose_native_chat.py
python scripts/evaluate_om_capabilities.py
```

Save the generated `docs/OM_ARCHITECTURE_AUDIT.md` and `artifacts/audit/om_architecture_audit.json` as build artifacts, not as proof of runtime correctness. Keep test logs and capability reports with the commit SHA and checkpoint/tokenizer fingerprints.

## Definition of done for OM overall

OM is not complete until all critical gates pass on the target deployment: exact model/tokenizer/checkpoint binding; coherent native generation; one observable gateway; multi-turn and tool/RAG correctness; security and privacy tests; reproducible training/evaluation; API/UX contract tests; and a rollback-capable release process. Cloud-frontier parity remains a measured research goal, not a software checklist item.
