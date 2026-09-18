# OM Companion Architecture

```
User → VoiceRuntime → CompanionBrain → Memory/Knowledge/Reasoning
     → ActionPlanner → Permission → Device/Agent Execute → Verify
     → Response → TTS → Avatar events (realtime)
```

## Packages

| Step | Package |
|------|---------|
| 40 | `om_ai/core/voice_intelligence` |
| 41 | `om_ai/core/companion_brain` |
| 42 | `om_ai/core/companion_memory` |
| 43 | `om_ai/core/companion_personality` |
| 44 | `om_ai/core/action_control` |
| 45 | `om_ai/core/companion_agent` |
| 46 | `om_ai/api/static/companion` |
| 47 | `om_ai/core/realtime` |
| 48 | `om_ai/core/device_runtime` |
| 49 | `om_ai/core/companion_security` |
| 50 | `om_ai/core/companion_runtime` |

Shared lifecycle: `CompanionRuntime` — one instance, not recreated per turn.
Brain answers route through existing ChatGPT runtime / chat intelligence (model-driven), not keyword reply tables.
