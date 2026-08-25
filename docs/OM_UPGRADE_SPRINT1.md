# OM Upgrade Sprint 1 — Execution (not analysis)

Built **running Python**, not another gap table.

```bash
om-ai upgrade sprint1
```

Report: `artifacts/OM_UPGRADE_SPRINT1_REPORT.json`

## Modules added

| Module | Path |
|--------|------|
| Self-Improvement Engine | `om_ai/improvement/` |
| Knowledge Factory | `om_ai/knowledge/factory.py` |
| Agent Runtime | `om_ai/agents/runtime.py` |
| Response Quality Intelligence | `om_ai/core/response/intelligence.py` |

## New commands

```bash
om-ai upgrade sprint1
om-ai improve --question "..." --answer "..."
om-ai agent-runtime --task "Add health check" --root .
```

## Loop (now real)

```text
Answer → Evaluate → Weakness → Training JSONL → Trainer queue → Version bump
```

Chat path: low-quality native replies are repaired + queued for improvement (`chat_backend` → `ensure_intelligent_response`).

Restart serve to load chat wiring:

```bash
om-ai serve --host 127.0.0.1 --port 8080
```
