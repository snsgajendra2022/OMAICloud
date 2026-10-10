# OM-1.0 native quality investigation — initial evidence

Date: 2026-10-10  
Repository branch: `feature/gpt5-production-runtime`

## Confirmed from repository inspection

1. `.env.example` selects the native backend and points to a local config, tokenizer, and checkpoint. It explicitly says the native checkpoint is experimental and does not claim frontier-model quality.
2. `tests/test_chat_empty_generation.py` tests empty/degenerate output and a deterministic greeting path. That greeting is a fallback and must not be counted as native model capability.
3. `scripts/evaluate_om_capabilities.py` currently defines 12 initial prompts and adds a separate context-retention follow-up result. It does not match the requested fixed set of 13 categories, and its deterministic keyword/format checks are smoke checks rather than complete semantic review.
4. `om_ai/runtime/chat_backend.py` contains output-rejection logic and explicitly avoids silently switching model providers. This is important protection, but rejection logic cannot make poorly trained weights coherent.
5. The checked-in README describes the native checkpoint as experimental. Checkpoint/tokenizer/config files are local artifacts under `artifacts/` and are not guaranteed to exist in a GitHub checkout.

## Likely failure chain (requires runtime confirmation)

The observed withheld response is consistent with native generation producing empty, repetitive, malformed, or otherwise low-quality text which is then rejected by the quality gate. This is a symptom-level explanation, not proof of the exact low-level defect. The specific cause must be confirmed by running inference against the exact local checkpoint and tokenizer while capturing pre-filter generated text and checkpoint metadata.

## Change made in this investigation

Added `scripts/evaluate_om_native_13_cases.py` and focused unit tests. The new harness:
- Defines exactly the 13 requested capability categories.
- Explicitly loads the configured native checkpoint and does not call a hosted model.
- records model/checkpoint/tokenizer identity, final answers, deterministic checks, failures, and timing in a JSON report.
- Marks semantic human review as required; deterministic checks alone do not promote a model.
- Does not count fallback output as a pass.
- Exits nonzero on failed cases and writes a report when inference can run.

## Not yet verified

No model generation, corpus audit, training, frontend test, SQLite concurrency test, full pytest run, or GitHub Actions run is claimed by this document. The GitHub connector can commit source files, but it does not provide the local ignored model artifacts needed to reproduce inference in this environment. Current/candidate A/B scores and training outcomes therefore remain pending until the required local artifacts and compute are available.

## Local reproduction

```bash
git checkout feature/gpt5-production-runtime
git pull origin feature/gpt5-production-runtime
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_om_native_13_case_evaluation.py
python scripts/evaluate_om_native_13_cases.py \
  --config configs/om-1.0-local.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt \
  --output artifacts/evaluations/om-native-current-13.json
```

For a candidate comparison, pass its own config/tokenizer/checkpoint explicitly and use a different output path. Do not overwrite the current checkpoint. A nonzero evaluation exit is a real failure, not a reason to weaken the checks.
