# OM Production Foundation — Complete Mode

Target: **everything around the model is built and verified**.

**Next full build (13-layer Cognitive OS):** paste  
[`docs/prompts/OM_AI_GENESIS_PLATFORM_PRODUCTION_MASTER_PROMPT.md`](prompts/OM_AI_GENESIS_PLATFORM_PRODUCTION_MASTER_PROMPT.md)  
into a new Cursor Agent chat.

```bash
om-ai system build
```

Report: `artifacts/SYSTEM_BUILD_REPORT.json`

## Verified commands

```bash
om-ai knowledge status
om-ai knowledge ingest path/to/file.txt
om-ai reason "Design a school management system"
om-ai evaluate run
om-ai continuous export
om-ai system check
```

## APIs

- `GET /health` → `{status: healthy, om_version: 1.0}`
- `POST /api/knowledge/upload|search`
- `POST /api/reasoning/analyze`
- `POST /api/evaluation/run`
- `POST /api/learning/feedback`

## External only

OM-1B / 7B / 70B **weight files** still need GPU + licensed data volume.  
The software path (configs, datasets layout, eval, learning, APIs) is complete.
