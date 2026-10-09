# OM Native Capability Upgrade Plan

## Goal

Build OM into a self-hosted AI product with broad capabilities comparable in *coverage* to modern cloud AI assistants, while keeping inference on OM-owned/self-hosted model weights and never silently falling back to a hosted LLM.

This is an engineering and model-training program, not a promise that current weights are already equivalent to a frontier model. Capability parity must be measured on named benchmarks and real user tasks.

## Current verified baseline

- The repository has a native decoder-only Transformer, tokenizer/training pipelines, a native inference backend, chat runtime, companion UI, retrieval/memory and agent/tool foundations.
- The repository's README explicitly states that architecture presets are not trained 1B/7B/13B/70B brains.
- The local diagnostic previously reported a missing `configs/om-1.0-production.json` while a tokenizer and checkpoint file existed. That path mismatch prevents loading before answer quality can even be evaluated.
- A file's existence or size does not prove that its weights are compatible or capable.

## Workstream 0 — Make native inference trustworthy

1. Fix the environment override so `OM_MODEL_CONFIG`, tokenizer and checkpoint point to one compatible run.
2. Run `python scripts/diagnose_native_chat.py`; require a successful load and non-empty outputs.
3. Run targeted tests before the full test suite. If the full suite is killed, split tests by module and inspect memory pressure rather than treating it as a pass.
4. Add regression tests for missing config, missing tokenizer, missing checkpoint, vocabulary mismatch, architecture mismatch and no-hosted-fallback behavior.
5. Record exact config/tokenizer/checkpoint hashes in a model manifest for every promoted model.

## Workstream 1 — Build a real capability evaluation suite

Evaluate a frozen OM checkpoint against a named reference model using identical held-out tasks. Include at minimum:

- General instruction following and multi-turn conversation
- Factual QA and uncertainty calibration
- Arithmetic, logic and multi-step reasoning
- Code generation, repair, tests and repository-level changes
- Long-context retrieval and conversation memory
- Tool selection, tool-call correctness and task completion
- Safety, prompt injection resistance and refusal behavior
- Latency, tokens/second, memory use, crash rate and repeatability

Store prompt IDs, model/checkpoint hashes, outputs, expected answers or rubrics, scores and error categories in machine-readable reports. Avoid training/evaluation data leakage. Do not report a single “100% parity” number unless the evaluation design and results justify it.

## Workstream 2 — Train for capability, not just UI behavior

1. Audit all training corpora for licensing, quality, duplication, contamination, language balance and code quality.
2. Build a reproducible tokenizer/model/checkpoint manifest; never combine a tokenizer and checkpoint from different runs.
3. Pretrain at a model scale justified by the available GPU memory, interconnect, storage, dataset and budget.
4. Run supervised fine-tuning on high-quality instruction, multi-turn, coding, tool-use and structured-output data.
5. Apply preference optimization/alignment only with meaningful chosen/rejected pairs and quality controls. Randomly selecting a bad response as the rejected answer is not a substitute for reliable preference labels.
6. Add continued training only when evaluation shows a specific capability gap; keep a frozen baseline and compare every candidate before promotion.

A 20M-parameter local checkpoint is useful for pipeline smoke tests, but should not be expected to match a frontier cloud model. Larger training requires appropriate GPU infrastructure and large, legally usable corpora; Mac CPU/MPS smoke runs do not produce a frontier-scale model.

## Workstream 3 — Add capability modules around the model

- **Memory:** explicit user controls, persistence boundaries, deletion/export, tenant isolation and retrieval tests.
- **Knowledge/research:** citations, source timestamps, source quality checks, contradiction handling and clear separation of retrieved text from trusted instructions.
- **Tools/agents:** typed tool schemas, permissions, timeouts, budgets, sandboxing, audit logs and post-action verification.
- **Coding:** repository indexing, patch-based edits, isolated test execution and rollback on failed changes.
- **Multimodal:** separate vision/speech models and evaluation until OM has compatible trained multimodal weights; a router alone is not multimodal intelligence.
- **Reliability:** useful errors, bounded retries, context budgeting, cancellation, streaming and graceful handling of unavailable tools.

These modules improve product coverage but cannot replace the language model's learned reasoning and generation abilities.

## Workstream 4 — Promotion gates

A candidate can be promoted only when:

- Its exact tokenizer, config and checkpoint are recorded and compatible.
- Native-only tests prove no hosted provider is called.
- The benchmark report is reproducible and compared with the previous checkpoint.
- Critical capability categories do not regress beyond agreed thresholds.
- Safety, latency, memory and failure-rate gates pass.
- The model card states known limitations and the tested hardware.

## Immediate next action

From the repository root, inspect the environment override and run the updated preflight diagnostic:

```bash
grep -nE '^(OM_MODEL_CONFIG|OM_AI_CONFIG|OM_MODEL_TOKENIZER|OM_AI_TOKENIZER|OM_MODEL_CHECKPOINT|OM_AI_CHECKPOINT)=' .env 2>/dev/null
python scripts/diagnose_native_chat.py
```

The diagnostic now reports missing assets and lists available config files before allocating model memory. Choose a config only after confirming that it matches the checkpoint's architecture and tokenizer vocabulary.
