# OM Companion Voice

## Components

- Device enumeration (`sounddevice` optional)
- Local wake-word phrase gate
- Energy VAD
- Streaming STT (`faster-whisper` / `whisper` / OM hooks)
- Streaming TTS (`say` / `pyttsx3` / OM TTS)
- Barge-in interruption while speaking

## Modes

- Full voice when audio deps + hardware present
- `--text-only` for brain/actions without mic

## Env

```
OM_COMPANION_WAKE_WORD=hey om
OM_COMPANION_WAKE_WORD_ENABLED=1
OM_COMPANION_STT_PROVIDER=auto
OM_COMPANION_TTS_PROVIDER=auto
```
