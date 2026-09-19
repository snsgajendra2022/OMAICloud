# OM → Tony Stark / Jarvis — Honest Path

You were right: a cyan orb + `macOS say` is a **JARVIS UI prototype**, not a personal AI entity.

## What we built in this pass

| Layer | Package / asset | Status |
|-------|-----------------|--------|
| Human conversation | `om_ai/core/human_conversation/` | Live — tired / problem / morning replies like a companion |
| Hinglish semantics | `om_ai/core/language_intelligence/` | Live — reminder / continue / open intents |
| 3D presence | `om_ai/api/static/companion/presence3d.js` | Live — Three.js procedural humanoid (eyes, jaw, breath, glow) |
| Neural TTS hook | `om_ai/core/voice_engine/neural_tts.py` | Ready — ElevenLabs / OpenAI when keys set |
| Companion OS | `om_ai/core/companion_os/` | Wires presence + conversation + language into every turn |

## What still is NOT movie Jarvis

| Gap | Reality |
|-----|---------|
| MetaHuman / Unreal 5 | Separate app + Live Link — not inside this Python repo yet |
| True British butler clone | Needs ElevenLabs / Fish voice clone + API key |
| Full facial blendshapes | Current 3D is a stylized presence body — upgrade path: VRM/GLB |
| Screen vision | Permission-gated stubs |

## How to get closer tonight

### 1. Neural British voice (biggest feel upgrade)

```bash
# .env
OM_NEURAL_TTS_PROVIDER=elevenlabs
OM_NEURAL_TTS_API_KEY=your_key
OM_NEURAL_TTS_VOICE_ID=your_british_butler_voice_id
OM_NEURAL_TTS_MODEL=eleven_multilingual_v2
```

Restart API. `/api/companion/tts` prefers neural; falls back to Daniel.

### 2. Use the 3D presence page

Hard-refresh: `http://127.0.0.1:8767/companion`

You should see a **3D figure** (not only the old orb). Presence modes drive head / eyes / jaw.

### 3. Next hardware/software leap (recommended)

```
Unity or Unreal MetaHuman  ←→  WebSocket  ←→  OM Companion OS (Python)
         body / face / lips                    brain / memory / agents
```

Keep the brain in OM. Put the body in a real 3D engine.

## Target feel checklist

- [x] Not only single-line chatbot replies for human moments (tired / problem)
- [x] Hinglish reminder understanding path
- [x] 3D character presence on web
- [x] Neural TTS adapter
- [ ] Paid neural voice configured
- [ ] VRM/MetaHuman body
- [ ] Projector / desk HUD (physical)

## Honest bottom line

OM is moving from **voice chatbot + HUD** toward **personal AI companion OS**.  
Movie-level Jarvis needs **neural voice + real 3D character + relationship memory over time** — we scaffolded those layers; the paid voice + MetaHuman body are the remaining external materials.
