# OM AI Capability Completion Gates

This document is the operational checklist for advancing OM AI toward reliable, measurable capability. "100%" means every agreed release gate passes for a stated scope; it does **not** mean guaranteed parity with every cloud model or guaranteed AGI.

## 1. Automated software gates

- [ ] Targeted native chat regression tests pass.
- [ ] Full Python test suite passes; failures are fixed or explicitly triaged with a tracked issue.
- [ ] Static analysis and type checks run where configured.
- [ ] Native provider is selected explicitly and no hidden hosted-provider fallback occurs.
- [ ] Missing config/tokenizer/checkpoint errors are actionable and fail before expensive inference.
- [ ] Checkpoint, config, and tokenizer identity are recorded in every evaluation report.
- [ ] Security tests cover authentication, tenant isolation, prompt injection, SSRF, tool permissions, rate limits, and secret handling.
- [ ] UI/API tests cover streaming, cancellation, timeouts, retries, malformed requests, and unavailable model assets.

## 2. Native asset gate (must run on the machine holding the weights)

From the repository root, with the project's virtual environment activated:

```bash
python scripts/diagnose_native_chat.py
python scripts/evaluate_om_capabilities.py
```

A model-load success is not a quality pass. Review each generated answer and confirm the report identifies the expected checkpoint, tokenizer fingerprint, config, device, and parameter count. If any asset is missing or mismatched, stop and correct the path; do not invent or download weights silently.

## 3. Capability evaluation gate

Keep a frozen test set that is not used for training. Include:

- Instruction following and multi-turn consistency
- Factual question answering and calibrated uncertainty
- Arithmetic, logic, and multi-step reasoning
- Code generation, code repair, and executing generated tests in a sandbox
- Context retrieval and explicit memory write/read/delete behavior
- Tool selection, permission enforcement, timeout behavior, and verified completion
- Safety, prompt-injection robustness, privacy, and refusal correctness
- Latency, throughput, peak memory, crash rate, and repeatability

For each run, save the model/checkpoint hash, tokenizer fingerprint, config, dataset version, prompt IDs, raw outputs, deterministic checks, human rubric scores, latency, and failures. Compare each candidate to the frozen baseline. Do not turn smoke-test pass rates into claims of cloud-model parity.

## 4. Real training gate

1. Confirm all training data is legally usable and audit quality, duplicates, PII, contamination, language coverage, and code licenses.
2. Establish a reproducible tokenizer/config/checkpoint manifest.
3. Choose model scale based on measured GPU memory, compute budget, storage, and target latency.
4. Train and validate a base model; preserve the baseline checkpoint.
5. Run supervised instruction tuning with high-quality examples and held-out validation.
6. Use preference optimization only with reviewed, trustworthy preference pairs.
7. Evaluate on untouched tasks and run safety/reliability tests before candidate promotion.
8. Promote only with a recorded report and rollback path.

A local ~20M-parameter checkpoint is a pipeline/debugging asset, not a substitute for the training and compute needed for frontier-grade language ability. A source-code change cannot create trained weights, licensed corpora, or GPU time.

## 5. Product completeness gate

- [ ] Memory has clear consent, tenant isolation, export, and deletion tests.
- [ ] Retrieval/research shows sources and dates, handles conflicts, and treats retrieved text as untrusted data.
- [ ] Tools have typed schemas, least-privilege permissions, sandboxing, budgets, audit logs, and post-action verification.
- [ ] Multimodal features are enabled only when compatible trained vision/speech models and datasets exist.
- [ ] Release docs disclose tested hardware, supported models, known limitations, and reproducible setup steps.
- [ ] Deployment has health checks, observability, backup/restore, rate limits, secrets management, and rollback.

## 6. Completion reporting

Report status by gate: **PASS**, **FAIL**, **BLOCKED (external asset/compute/data required)**, or **NOT RUN**. Never label the entire system "100% complete" while a required gate is failed, blocked, or untested. Re-run the full suite and capability evaluation for each candidate checkpoint.
