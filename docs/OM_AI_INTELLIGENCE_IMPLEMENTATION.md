# OM AI Intelligence Implementation Plan

## Purpose

This document defines staged engineering work for intent understanding, emotion-aware communication, answer verification, memory, language support, coding intelligence, and safe tool use. It is not a claim that every capability is implemented or that current native weights have frontier-model quality.

## Initial code slice

- `om_ai/core/intelligence_contract.py` provides deterministic routing hints for common request types.
- Emotion labels are uncertain cues, not diagnoses or claims that the model has human feelings.
- Consequential actions are flagged for authorization and confirmation checks.
- `assess_answer_quality` checks basic response integrity; it does not prove factual correctness.
- Original user text is preserved.
- These functions are a foundation and are not yet connected to the production chat path.

Run tests with `pytest -q tests/test_intelligence_contract.py`.

## Priority 0: Native model reliability

1. Reproduce raw base and SFT generation failures.
2. Validate checkpoint architecture, tokenizer fingerprint, vocabulary, special token IDs, chat template, context length and stop tokens.
3. Audit pretraining/SFT labels, shifts, masks, document boundaries and loss computation.
4. Record training and validation loss, token counts, configuration and checkpoint provenance.
5. Test tiny-dataset overfit, checkpoint save/load/resume and deterministic generation.
6. Do not launch another long training run until the data and training pipeline are verified.

## Workstreams

### Intent and ambiguity
Preserve the original message; infer likely intent from text and context; detect missing constraints; ask one focused question when interpretations materially differ; handle typos, shorthand, transliteration and mixed languages.

### Emotion-aware interaction
Use contextual cues to select a respectful tone. Treat emotion as uncertain, avoid diagnosis or manipulation, and implement and test safe responses to distress.

### Reasoning and planning
Use adaptive effort for simple versus complex requests. Define task steps, constraints, budgets and completion conditions. Use executable tools for exact calculations and tests for code. Provide useful conclusions and evidence without exposing private internal reasoning.

### Verification and repair
Use separate verification for calculations, code, citations, summaries, translations, formatting and tool results. Bound retries. If checks fail, repair, clarify, abstain or explain the limitation. A non-empty answer is not proof of correctness.

### Memory and personalization
Separate current context, conversation history, summaries and long-term memory. Provide user controls for viewing, editing, disabling, exporting and deleting memory. Enforce tenant isolation and track provenance/freshness.

### Languages and coding
Start evaluation with English, Hindi, Romanized Hindi and Hinglish. Evaluate comprehension, writing, translation, code-switching and speech separately. Build coding tests across advertised languages and frameworks; inspect repository diffs and run tests before claiming a fix works.

### Knowledge, tools and multimodality
Add permission-aware retrieval and citations. Validate tool arguments, permissions, timeouts, budgets and audit trails. Treat retrieved content as untrusted data. Add vision, audio and video only with compatible models and separate evaluations.

### Production readiness
Track model, tokenizer, config, data and code versions. Measure task success, factuality, calibration, repair rate, safety, latency, throughput, memory and cost. Keep regression tests and rollback paths. Document limitations.

## Required evaluation categories

1. Clear, misspelled and ambiguous intent.
2. User corrections and multi-turn context.
3. Emotion cues and respectful tone.
4. Logical and mathematical correctness.
5. Code generation, debugging, tests and security.
6. Research grounding and citation validity.
7. Memory freshness and tenant isolation.
8. English, Hindi, Hinglish and each advertised language.
9. Tool errors, retries, cancellation and consequential actions.
10. Prompt injection, privacy and authorization.
11. Latency, resource limits and regressions.

## Status

- [x] Add deterministic intent/emotion routing contract.
- [x] Add basic answer-integrity checks with explicit limitations.
- [x] Add focused contract tests.
- [ ] Run tests in the repository environment.
- [ ] Integrate the contract into the actual chat path.
- [ ] Diagnose and evaluate native generation.
- [ ] Implement domain-specific independent verification.
- [ ] Complete remaining workstreams.

Update this status only when code and tests support the change. A committed module is not a fully integrated or production-ready intelligence system.
