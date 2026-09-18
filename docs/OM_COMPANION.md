# OM Companion Runtime

Voice-first, local-first personal AI companion for OM AI.

## Quick start

```bash
source .venv/bin/activate
om-ai companion doctor
om-ai companion start --text-only
```

Open avatar UI (with `om-ai serve` running):

- http://127.0.0.1:8080/companion

## Commands

| Command | Purpose |
|---------|---------|
| `om-ai companion start` | Start runtime |
| `om-ai companion start --text-only` | No mic/TTS hardware |
| `om-ai companion start --no-wake-word` | Skip wake gate |
| `om-ai companion start --no-avatar` | Backend only |
| `om-ai companion stop` | Clean shutdown |
| `om-ai companion status` | Banner / state |
| `om-ai companion doctor` | PASS/WARN/FAIL checks |
| `om-ai companion devices` | Microphones/speakers |
| `om-ai companion permissions` | Action audit |
| `om-ai companion memory` | List memory (`--clear`) |
| `om-ai companion config` | Env-derived settings |

## Wake phrase

Default: `hey om` (`OM_COMPANION_WAKE_WORD`)

## Architecture docs

- [Architecture](OM_COMPANION_ARCHITECTURE.md)
- [Security](OM_COMPANION_SECURITY.md)
- [Voice](OM_COMPANION_VOICE.md)
- [Actions](OM_COMPANION_ACTIONS.md)
- [Troubleshooting](OM_COMPANION_TROUBLESHOOTING.md)
