# OM Companion Troubleshooting

| Symptom | Fix |
|---------|-----|
| `sounddevice` missing | `pip install sounddevice` or use `--text-only` |
| STT unavailable | `pip install faster-whisper` (or whisper) |
| TTS unavailable | macOS `say` is used by default; or install `pyttsx3` |
| Waiting for wake | Say `hey om` or start with `--no-wake-word` |
| Companion API 404 | Restart `om-ai serve` after upgrade |
| Import errors | Use `.venv/bin/python` / activated venv |

Run diagnostics:

```bash
om-ai companion doctor
```
