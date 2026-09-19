# OM Companion Page — Full Details

**URL:** `http://127.0.0.1:8767/companion`  
(also works on `http://127.0.0.1:8080/companion` when that serve process is running)

**Source UI:** `om_ai/api/static/companion/index.html`  
**API:** `om_ai/api/companion/routes.py` → `/api/companion/*`  
**Brain:** `om_ai/core/companion_runtime/` + `om_ai/core/companion_brain/`  
**Voice:** `om_ai/core/voice_intelligence/` + `om_ai/core/companion_personality/voice_presence.py`

---

## What this page is

A **voice-first Jarvis-style companion**, not a chat box.

- **Primary visual:** cyan **HUD orb** (rotating rings + white particle emission core)
- Always-on listening after one mic enable
- You speak → OM hears → human conversation / Hinglish brain → speaks back
- Screen shows: **You said** · **Feeling** · **OM** reply · Memory · Activity

Hard-refresh after upgrades: `http://127.0.0.1:8767/companion` (or `:8080/companion`)

Brain upgrades (consciousness, dialogue, memory) stay — the avatar look stays the classic orb.

---

## Page layout (DOM)

| Element | Role |
|--------|------|
| `.brand` **OM** | Product mark |
| `#privacyHint` | “Always listening · speak naturally” |
| `#orbWrap` | HUD container (`data-state`: idle / listening / thinking / speaking / muted) |
| `#auraCanvas` | Outer faint particle halo |
| SVG `.hud-svg` | Rotating cyan rings + gold accent |
| `#orb` / `#coreCanvas` | Core orb with live **white emission** particles |
| `#stateLabel` | ALWAYS LISTENING / SPEAKING / … |
| `#wave` | Small cyan activity bars |
| `#livePill` | “Always listening — just speak” |
| `#heard` | What you said |
| `#feeling` | Affect label (neutral / warm / concerned / …) |
| `#reply` | What OM says (spoken aloud) |
| `#activity` | Short brain activity trail |
| `#btnEnable` | One-time mic gate (browser requirement) |
| `#micHelp` | Shown if mic blocked |
| `#permBox` | Rare action-permission yes/no |

---

## Visual system (Jarvis HUD)

- Background: deep charcoal-blue (`#050a10`)
- Primary cyan: `#75d5e3` / bright `#b8f4ff`
- Gold accent on ring: `#d4af37`
- Outer aura canvas: drifting cyan/white dots
- Core canvas: dense white particle emission + rim glow
- Rings rotate CW / CCW at different speeds; pulse while thinking
- Speaking: core brightens + particle energy boost (not a cartoon face)

---

## Voice flow (end-to-end)

```
Mic (Web Speech API)
  → interim text in #heard
  → final utterance → POST /api/companion/message
  → CompanionRuntime.handle_text
       → Companion Brain (social / semantic / model)
       → voice_presence.shape_for_speech (Jarvis cadence)
  → response: { heard, answer, spoken, spoken_tts, feeling, … }
  → UI shows You said + OM
  → POST /api/companion/tts → macOS `say` WAV (Daniel / Rishi)
  → play audio; barge-in possible while speaking
  → return to always-on listen
```

### Key API routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/companion/session` | Start session + greeting |
| POST | `/api/companion/message` | Text turn (from STT) |
| POST | `/api/companion/tts` | Synthesize speech audio |
| POST | `/api/companion/interrupt` | Stop speech / barge-in |
| POST | `/api/companion/hear` | Upload audio → STT → reply |
| GET | `/api/companion/status` | Runtime banner |

---

## Personality & language

Configured in `voice_presence.py`:

- Speaks like **Jarvis**: calm, loyal, sharp, addresses you as **Sir**
- Hindi / Hinglish: natural mix — *Haan sir, boliye — kya baat hai?*
- English: short spoken lines, then a follow-up question
- Never asks to “rephrase in one short sentence”
- Affect labels surface as **Feeling · …** on the page

---

## TTS (voice sound)

| Setting | Default | Notes |
|---------|---------|--------|
| `OM_COMPANION_TTS_VOICE` | `Daniel` | UK male — closest built-in “Jarvis” tone on macOS |
| `OM_COMPANION_TTS_RATE` | `158` | Slightly slower = calmer, less “read aloud” |
| Hindi/Hinglish auto | `Rishi` / `Lekha` | Picked when reply locale is `hi` |

True movie-Jarvis (Paul Bettany neural clone) is **not** available as a free system voice. Daniel + pacing + Jarvis dialogue style is the practical macOS path. For closer clones, plug a premium TTS later (ElevenLabs / custom voice) into `SpeechSynthesizer`.

---

## How to run

```bash
cd "/Users/gajendrarawat/Downloads/om-ai-operating-brain 3"
source .venv/bin/activate
# if 8080 is taken by Apache, use 8767:
uvicorn om_ai.api.main:app --host 127.0.0.1 --port 8767
```

Open: **http://127.0.0.1:8767/companion**  
Use **Chrome or Safari**, allow microphone once, then just talk.

Hard refresh after UI changes: `Cmd+Shift+R`.

---

## States you will see

| State | Meaning |
|-------|---------|
| Starting | Session boot |
| ALWAYS LISTENING | Mic open — speak anytime |
| UNDERSTANDING / thinking | Brain turn |
| SPEAKING | TTS playing; HUD core bright |
| WAITING_FOR_PERMISSION | Rare device/action gate |
| Mic blocked | Browser denied mic — follow `#micHelp` |

---

## Files that own this experience

```
om_ai/api/static/companion/index.html          # page UI + always-on listen
om_ai/api/companion/routes.py                  # HTTP/WebSocket API
om_ai/api/main.py                              # mounts /companion
om_ai/core/companion_runtime/companion_runtime.py
om_ai/core/companion_brain/companion_runtime.py
om_ai/core/companion_personality/voice_presence.py
om_ai/core/voice_intelligence/speech_synthesizer.py
artifacts/companion/memory.json                # episodic companion memory
.env                                           # OM_COMPANION_TTS_* 
```

---

## Design intent (what “real Jarvis” means here)

1. **Listen continuously** — no tap every turn  
2. **Talk back** — short spoken replies, not essays  
3. **Address you** — *Sir* / respectful Hinglish  
4. **Ask back** — *Boliye, kya baat hai?* / *What should we take on?*  
5. **Feel present** — HUD reacts; feeling label; barge-in  
6. **Mirror language** — Hindi in → Hinglish out; English in → English out  

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Mic not allowed | Chrome → site settings → Microphone Allow; use `127.0.0.1` not `file://` |
| Old robotic “rephrase” line | Restart `uvicorn` so Python picks up `voice_presence` / optimizer fixes |
| Flat “reading lines” voice | Confirm `OM_COMPANION_TTS_VOICE=Daniel` and rate ~158; hard-refresh page |
| Apache owns 8080 | Use port **8767** as above |
| No audio | Check `/api/companion/tts` returns WAV; macOS `say -v Daniel` works in Terminal |

---

*Last updated for the voice-first Jarvis HUD companion build.*
