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

## Latest local result supplied by the developer

On 2026-10-10, the configured current checkpoint was evaluated with `scripts/evaluate_om_native_13_cases.py`:

- Cases: 13
- Passed: 1
- Failed: 12
- Release ready: false
- Hosted fallback used: false
- Runtime repeatedly logged: `OM native generation rejected as degenerate token soup`

This is direct evidence of a native generation-quality failure, but it does not identify whether the cause is training quality, tokenizer/weight mismatch, or an inference defect. The JSON evaluation report was created locally at `artifacts/evaluations/om-native-current-13.json`; its contents have not been provided to the repository tooling.

## Next diagnostic required

The local diagnostic script now accepts explicit config/tokenizer/checkpoint paths, emits first-step logit health and raw generated token IDs/text before quality filtering, and can save a JSON report. Run it with the same assets used for the failed evaluation:

```bash
python scripts/debug_native_generation.py \
  --config configs/om-1.0-local.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt \
  --prompt "How are you?" \
  --max-new-tokens 64 \
  --output artifacts/evaluations/om-native-raw-debug.json
```

Inspect these fields first: `checkpoint_metadata`, `tokenizer_info`, `tokenizer_fingerprint`, `first_next_token_logits_finite`, `first_next_token_top_logits`, `generated_token_ids`, and `raw_candidate`. The raw report can contain generated/user text; keep it local and do not commit private conversation data.

## Not yet verified

No new model generation or training run was performed by the repository editing tool. The developer-provided 13-case run is recorded above. Corpus audit, frontend test, SQLite concurrency test, full pytest run, and completed GitHub Actions run are not claimed by this document. The GitHub connector can commit source files, but it does not provide the local ignored model artifacts needed to reproduce inference in this environment. Current/candidate A/B scores and training outcomes therefore remain pending until the required local artifacts and compute are available.

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
