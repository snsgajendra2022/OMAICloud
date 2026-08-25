# OM AI Foundation Upgrade v1.0

Additive software foundation. Does **not** replace existing `om_ai/` packages.

## Modules

| Spec | Location |
|---|---|
| Reasoning (analyze→plan→solve→verify→reflect) | `om_ai/core/reasoning/` |
| Document ingestion | `om_ai/knowledge/ingestion/` |
| Vector retrieval | `om_ai/knowledge/retrieval/` |
| Evaluation | `om_ai/evaluation/` |
| Learning | `om_ai/learning/` |
| Upgrade runner | `om_ai/foundation/` |
| APIs | `om_ai/api/foundation_routes.py` |

## One command

```bash
om-ai upgrade foundation
```

Creates folders, knowledge-universe layout, training prep, runs eval, writes:

`artifacts/FOUNDATION_UPGRADE_REPORT.json`

## APIs

- `POST /api/knowledge/upload`
- `POST /api/knowledge/search`
- `POST /api/reasoning/analyze`
- `POST /api/evaluation/run`
- `POST /api/learning/feedback`
- `POST /api/learning/export`

## Remaining external

OM-1B / 7B / 70B **weights** still need licensed data + GPU. Path is ready via `training/` + `configs/om-1b.json` etc.
