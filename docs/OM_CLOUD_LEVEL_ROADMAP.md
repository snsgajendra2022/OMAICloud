# OM AI Capability Upgrade Plan

## Goal

Improve OM AI as a self-owned native model through measured engineering, training, evaluation, and deployment. This plan does **not** claim parity with ChatGPT or any cloud frontier model. Parity claims require reproducible benchmark results.

## Local development profile

For an Apple M4 Mac with 48 GB or more unified memory, begin with `configs/om-m4-48gb.json`. It is a small native model profile intended to validate the pipeline and early experiments. It is not a production assistant checkpoint.

Start with a short FP32 run, verify checkpoint reload, then test mixed precision only if loss remains finite. Keep batch size 1, context 512, gradient accumulation 8, and gradient checkpointing enabled until measured memory/throughput justifies changes.

## Upgrade gates

### Gate 1 — Reproducible baseline
- Record branch commit, Python/PyTorch versions, device, config, tokenizer fingerprint, and dataset audit.
- Run native diagnostics and capability evaluation before training.
- Save baseline outputs so later results can be compared.

### Gate 2 — Reliable native training
- Verify finite loss, backward pass, optimizer step, checkpoint write/reload, resume behavior, and deterministic evaluation where supported.
- Track training and validation loss separately.
- Log tokens/second, step time, and available MPS memory metrics when supported.
- Keep checkpoint retention bounded and preserve one known-good checkpoint.

### Gate 3 — Data quality and tokenizer
- Use only data with documented permission/license and explicit training approval.
- Deduplicate and filter low-quality, contaminated, or private data.
- Keep held-out validation and test sets separate from training.
- Measure tokenizer coverage on the target languages and code before committing to a larger vocabulary.

### Gate 4 — Assistant tuning
- Prepare curated instruction-response examples with a consistent chat format.
- Run supervised fine-tuning only after base pretraining is validated.
- Add preference tuning only with reviewed chosen/rejected examples and regression tests.
- Do not train on raw user conversations without explicit consent, privacy controls, retention rules, and redaction.

### Gate 5 — Capability evaluation
Maintain fixed, versioned test sets for:
- General knowledge and factuality
- Multi-step reasoning and mathematics
- Code generation and executable tests
- English and Hindi instruction following
- Long-context retrieval and grounded answers
- Tool use, refusal behavior, privacy, and prompt-injection robustness
- Latency, throughput, memory, and reliability

Report sample counts, scoring method, confidence/variance where appropriate, model/checkpoint hash, and baseline comparison. Avoid cherry-picking results.

### Gate 6 — Production readiness
- Verify serving behavior, streaming, timeouts, cancellation, concurrency, and resource limits.
- Add model/checkpoint/tokenizer compatibility checks and rollback.
- Keep external hosted model fallback disabled unless the operator explicitly configures it.
- Test security, access control, data handling, and failure recovery.
- Publish a model card stating training sources, limitations, benchmark results, and known risks.

## Compute reality

A local Mac is useful for software validation, tokenizer/corpus preparation, small-model experiments, and inference. It is not a realistic single-machine route to pretraining a frontier-scale model from scratch. Large-scale capability requires substantially more approved training data, compute, engineering, and iteration. A licensed pretrained model can be a separate route to stronger local performance, but its upstream weights must be disclosed as such and it is not scratch-trained OM weights.

## Acceptance criteria

Do not mark an upgrade complete until tests pass and a before/after report demonstrates the change. Do not claim cloud-level parity without independent, reproducible benchmarks.
