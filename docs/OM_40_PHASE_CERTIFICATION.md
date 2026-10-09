# OM AI Phases 25–40: Certification Gates

This document extends the 24-phase implementation program. Certification phases are evidence gates, not a promise that every capability already works. A gate can be **PASS**, **FAIL**, or **BLOCKED**. Missing evidence is BLOCKED, never PASS.

## First executable gate

Run locally from the repository root:

```bash
source .venv/bin/activate
python -m compileall -q om_ai scripts
python -m pytest -q
python scripts/audit_om_architecture.py
python scripts/certify_om_release.py --revision "$(git rev-parse HEAD)"
```

The certification script writes `artifacts/audit/om_release_certification.json`. It requires a real config, tokenizer, checkpoint, tokenizer round-trip, checkpoint load, and six usable native generations. It does not replace model output with templates. Its PASS is **smoke-only**, not semantic certification or frontier parity. A failing run returns exit code 2. Do not commit private `.env` values or local checkpoint weights as part of reporting the result.

## Phase register

| Phase | Certification gate | Evidence required | Status until evidence |
|---|---|---|---|
| 25 | System integration | Trace a request through API → conversation/context → retrieval/tools when needed → gateway/native model → quality gate; prove provenance and failure propagation | BLOCKED |
| 26 | Model | Exact checkpoint hash; architecture/config; strict weight load; finite forward logits; parameter count; device recorded | BLOCKED |
| 27 | Tokenizer | Vocabulary and special-token IDs match model embeddings/LM head; fingerprint bound to checkpoint; multilingual round-trip properties | Partial preflight implemented |
| 28 | Real generation | Native-only fixed prompts, raw outputs, no degenerate text, latency, semantic review; no hidden hosted/template substitution | Smoke harness implemented; quality gate pending |
| 29 | Conversation | Multi-turn reference, topic, task, correction, and continuation tests with saved test transcript | BLOCKED |
| 30 | Memory | Cross-session recall, relevance, deletion/retention, consent, and tenant-isolation tests | BLOCKED |
| 31 | RAG | Relevant and irrelevant retrieval sets, source citations, reranking, no-evidence abstention, source provenance | BLOCKED |
| 32 | Reasoning | Held-out math, constraint, debugging, planning and verification cases with deterministic scoring where possible | BLOCKED |
| 33 | Agents/tools | Allow-list, schema validation, authorization, timeout, result validation, audit logs and malicious-input tests | BLOCKED |
| 34 | Multimodal | Per-modality load/compatibility checks and evaluation; unsupported modalities fail explicitly rather than claiming capability | BLOCKED |
| 35 | Safety/security | Prompt injection, secret leakage, tenant isolation, unsafe tool calls, poisoned retrieval and malicious file tests | BLOCKED |
| 36 | Performance/scale | Repeatable concurrency test with p50/p95/p99 latency, TTFT, tokens/sec, resource metrics and error rate on declared hardware | BLOCKED |
| 37 | Reliability | Fault injection for model, DB, RAG, tool, timeout and cancellation; no false success; retry/rollback evidence | BLOCKED |
| 38 | Continuous learning | Consent-aware feedback pipeline, reviewed dataset build, reproducible train/eval, promotion and rollback rehearsal | BLOCKED |
| 39 | Frontier benchmarking | Same versioned public/private evaluation set and scoring protocol for OM and reference models; disclose hardware and uncertainty | BLOCKED |
| 40 | Production release | All critical gates pass, signed artifact manifest, monitored rollout, SLOs, incident/rollback runbook | BLOCKED |

## Release rules

1. A successful import or HTTP 200 is not proof of usable model output.
2. A loaded checkpoint is not proof of semantic quality.
3. A smoke test is not a benchmark; a benchmark is not proof of frontier parity.
4. External providers are allowed only when explicitly configured and must be identified in provenance. In native-only certification they must not be called.
5. User conversations must not silently become training data. Dataset inclusion requires an explicit lawful basis, consent where required, privacy filtering, and review.
6. Never promote a model only because its version is newer. Promotion requires evaluation against the currently deployed model and a rollback artifact.
7. Certification output must preserve failures and raw generated text for diagnosis while redacting secrets and personal data.

## Immediate implementation sequence

1. Run the new release certification on the exact local checkpoint and save the sanitized report.
2. Fix the first failing compatibility/load/generation check; add a regression test for each defect.
3. Inventory every production request entry point and route generation through one typed gateway contract.
4. Add end-to-end conversation, memory, RAG and tool tests one subsystem at a time.
5. Run quality, security and performance suites before changing any gate to PASS.

The certification script currently checks artifact presence, tokenizer loading/round-trip, native checkpoint loading, and six basic native-generation smoke cases. The remaining phase rows are deliberately not represented as completed.
