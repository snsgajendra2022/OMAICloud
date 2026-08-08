# Model Registry

Module: `om_ai/registry/model_registry.py` — CLI: `om-ai registry`.

## Layout

```text
artifacts/registry/<version>/
  weights.pt
  tokenizer.json
  metadata.json   # state, checksum, benchmarks, provenance, trained flag
```

## Lifecycle states

`training` → `candidate` → `evaluated` → `approved` → `production` (or `deprecated` from most states). Transitions are enforced; skipping ahead is rejected.

## CLI

```bash
om-ai registry list --root artifacts/registry

om-ai registry register \
  --model-id v0.3-tiny-demo \
  --config configs/tiny.json \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/demo/om-tiny-dpo.pt \
  --data-version demo \
  --architecture om-transformer
# add --trained only when a real training run produced the weights
```

Bundles: `om-ai bundle` / `om_ai/checkpoint/bundle.py` (SHA256 integrity).

## Policy

- `trained=False` by default for honesty
- Attach eval/benchmark dicts before `approved` / `production`
- Tiny demo checkpoints must not be labeled as OM-7B/70B production brains
