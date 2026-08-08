# Continuous Learning

Package: `om_ai/continuous/` — `feedback.py`, `replay.py`.

## Feedback store

`FeedbackStore` (SQLite): prompt, response, rating, optional preferred response, metadata, user id.

```bash
om-ai feedback add \
  --prompt "…" --response "…" --rating 5 \
  --preferred-response "…"

om-ai feedback export \
  --sft-output artifacts/feedback_sft.jsonl \
  --preference-output artifacts/feedback_preferences.jsonl \
  --min-rating 4
```

Exports feed `om-ai sft` / `om-ai dpo` after human review.

## Practice

- Threshold ratings; exclude PII
- Version datasets; log provenance in the registry
- Re-evaluate after each replay fine-tune
- Continuous learning updates **checkpoints**, not magically the untuned 70B preset

API feedback endpoints (when enabled) share the same idea: capture → review → export → train → promote.
