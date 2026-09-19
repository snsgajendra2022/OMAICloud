# OM Companion Voice

## Honest limit

| Path | Feels like | Cost |
|------|------------|------|
| **macOS Daniel** (default) | Clear system butler — not real human | Free |
| **ElevenLabs / Azure** | Near-human neural | Paid (opt-in) |
| Film Jarvis clone | Not allowed (copyright) | — |

No code can make free `say` sound like a real person. We improve **delivery** (rate, pauses, text), not the vocal cords.

## Default (free)

```bash
OM_COMPANION_TTS_PROVIDER=macos
OM_COMPANION_TTS_VOICE=Daniel
OM_COMPANION_TTS_RATE=165
```

## Optional paid neural

```bash
OM_COMPANION_TTS_PROVIDER=elevenlabs
OM_NEURAL_TTS_PROVIDER=elevenlabs
OM_NEURAL_TTS_API_KEY=your_real_key
OM_NEURAL_TTS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
OM_NEURAL_TTS_MODEL=eleven_multilingual_v2
```

## Code map (single source of truth)

```
om_ai/core/voice_engine/
  tts_provider.py      # entry: get_voice_engine()
  human_delivery.py    # free-path conversational pacing
  voice_profiles.py    # settings (om_system default)
  voice_model.py       # optional neural synthesize
  realtime_tts.py      # optional ElevenLabs/Azure stream
  emotion_voice.py     # emotion knobs
  streaming_voice.py   # text chunks
  prosody_engine.py    # pauses
  lip_sync.py          # viseme / jaw frames
  voice_cloner.py      # authorized clone only (off)
```

Compat shims: `neural_tts.py`, `voice_provider.py`, `om_ai/core/neural_voice/*` → all call `voice_engine`.

## API

- `POST /api/companion/voice/plan` — plan (emotion, chunks, lips)
- `POST /api/companion/tts` — audio file (free say or neural)
- `POST /api/companion/tts/stream` — realtime (paid only)

Restart after `.env` changes: `om-ai start`
