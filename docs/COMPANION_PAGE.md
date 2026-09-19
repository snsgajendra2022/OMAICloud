# OM Companion Page — Full Details

**Primary URL:** `http://127.0.0.1:8080/companion`  
**Hard refresh / cache bust:** `http://127.0.0.1:8080/companion?v=hud4`  
(also works on another port if you start serve there, e.g. `8767`)

**Source UI:** `om_ai/api/static/companion/index.html`  
**Presence:** `om_ai/api/static/companion/presence3d.js` + `three.min.js`  
**API:** `om_ai/api/companion/routes.py` → `/api/companion/*`  
**Lifecycle:** `om_ai/core/companion_runtime/`  
**Brain:** `om_ai/core/companion_brain/`  
**OS enrich:** `om_ai/core/companion_os/`  
**Voice:** `om_ai/core/voice_engine/` + `om_ai/core/voice_intelligence/speech_synthesizer.py`  
**Speech style:** `om_ai/core/companion_personality/voice_presence.py`  
**Architecture (5 pillars):** [JARVIS_ARCHITECTURE.md](./JARVIS_ARCHITECTURE.md)

---

## What this page is

A **voice-first Jarvis-style companion**, not a chat box.

- **Primary visual:** cyan **HUD orb** (rotating rings + white particle core)
- Optional **3D presence** layer inside the orb (`OMPresence3D` / Three.js)
- Always-on listening after one mic enable
- You speak → OM hears → companion brain → speaks back (Aman / Indian male)
- Screen shows: **You said** · **Feeling** · **OM** reply · **Memory** · Activity

Hard-refresh after upgrades: `Cmd+Shift+R` on `?v=hud4`.

---

## Page layout (DOM)

| Element | Role |
|--------|------|
| `.brand` **OM** | Product mark |
| `#privacyHint` | “Always listening · just speak” / user name |
| `#orbWrap` | HUD container (`data-state`: idle / listening / thinking / speaking / muted) |
| `#auraCanvas` | Outer faint particle halo |
| SVG `.hud-svg` | Rotating cyan rings + gold accent |
| `#orb` / `#coreCanvas` | Core orb with live **white emission** particles |
| `#presence3d` | Mount point for procedural 3D figure + lip sync |
| `#stateLabel` | ALWAYS LISTENING / SPEAKING / … |
| `#wave` | Small cyan activity bars |
| `#livePill` | “Always listening — just speak” |
| `#heard` | What you said |
| `#feeling` | Affect label (neutral / warm / concerned / …) |
| `#reply` | What OM says (spoken aloud) — **never** internal agent dumps |
| `#memoryLine` | Live memory / purpose (e.g. `Working on ai development`) |
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
- Rings rotate CW / CCW; pulse while thinking
- Speaking: core brightens + particle energy; jaw driven by TTS lip plan when 3D is ready
- Static assets: `/static/companion/presence3d.js`, `/static/companion/three.min.js`

---

## Voice flow (end-to-end)

```
Mic (Web Speech API, en-IN / hi-IN)
  → interim text in #heard
  → final utterance
       → if "stop" / "ruk" / "band karo" … → cut audio immediately (no brain TTS)
       → else POST /api/companion/message
  → CompanionRuntime.handle_text
       → Companion Brain (semantic → response engine)
       → strip internal chrome (Agent[…], context dumps)
       → CompanionOS.enrich_turn (presence, memory, lips plan)
       → voice_presence / human_delivery (Aman pacing)
  → response: { heard, answer, spoken, spoken_tts, feeling, memory_line, … }
  → UI shows You said + OM (+ Feeling / Memory)
  → POST /api/companion/tts → macOS `say -v Aman` WAV
  → play audio + lip sync; barge-in while speaking
  → return to always-on listen
```

### Key API routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/companion/session` | Start session + dynamic greeting |
| POST | `/api/companion/message` | Text turn (from STT); `speak_client=false` on stop |
| POST | `/api/companion/tts` | Synthesize speech (Aman by default) |
| POST | `/api/companion/voice/plan` | Emotion / chunks / lip frames (no audio) |
| POST | `/api/companion/interrupt` | Stop speech / barge-in |
| POST | `/api/companion/hear` | Upload audio → STT → reply |
| GET | `/api/companion/status` | Runtime banner |

---

## Personality & language

Configured in `voice_presence.py` + `personality_rules.py`:

- Speaks like a calm personal companion — loyal, sharp, natural **Sir** / **Ji**
- Hindi / Hinglish mirrored when you speak that way
- English: short spoken lines (1–3 sentences)
- **No** canned “What should we work on next?” append after every short answer
- **No** agent/pipeline text spoken or shown (`Agent[memory]: …` is blocked)
- Affect labels surface as **Feeling · …** on the page

### Stop / interrupt

Say any of: `stop`, `cancel`, `quiet`, `mute`, `ruk`, `ruko`, `band karo`, `chup`, `bas`…

- Client cuts TTS **immediately** (even mid-sentence / mid-turn)
- Server returns a short confirm and **does not** re-trigger client speak

---

## TTS (voice sound)

| Setting | Default | Notes |
|---------|---------|--------|
| `OM_COMPANION_TTS_PROVIDER` | `macos` | Free local path |
| `OM_COMPANION_TTS_VOICE` | `Aman` | Indian male (`en_IN`) — clear companion voice |
| `OM_COMPANION_TTS_RATE` | `178` | Natural conversational pace |
| Soft / concerned | ~162 | Slightly slower |
| Excited | ~188 | Slightly faster |
| Devanagari-heavy | Aman → Rishi → Lekha | Keep male identity when possible |

Delivery lives in `om_ai/core/voice_engine/human_delivery.py` (light pauses, emotion knobs).  
Optional paid neural: set `OM_COMPANION_TTS_PROVIDER=elevenlabs` + API key (see `docs/JARVIS_VOICE.md`).

---

## How to run

```bash
cd "/Users/gajendrarawat/Downloads/om-ai-operating-brain 3"
source .venv/bin/activate
om-ai serve --host 127.0.0.1 --port 8080
```

Open: **http://127.0.0.1:8080/companion?v=hud4**  
Use **Chrome or Safari**, allow microphone once, then just talk.

Hard refresh after UI/Python changes: `Cmd+Shift+R` and restart serve so `.env` / Python modules reload.

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
om_ai/api/static/companion/index.html          # HUD UI + always-on listen + stop
om_ai/api/static/companion/presence3d.js       # 3D presence + lips
om_ai/api/static/companion/three.min.js        # Three.js (required locally)
om_ai/api/companion/routes.py                  # HTTP/WebSocket API
om_ai/api/main.py                              # mounts /companion + /static
om_ai/core/companion_runtime/companion_runtime.py
om_ai/core/companion_brain/companion_runtime.py
om_ai/core/companion_os/companion_os.py
om_ai/core/companion_personality/voice_presence.py
om_ai/core/voice_engine/tts_provider.py
om_ai/core/voice_engine/human_delivery.py
om_ai/core/voice_intelligence/speech_synthesizer.py
om_ai/core/conversation_runtime/conversational_flow.py   # topic only — no canned Qs
artifacts/companion/memory.json
artifacts/companion/human_memory/              # episodic / emotional / projects
.env                                           # OM_COMPANION_TTS_* = Aman / 178
```

---

## Readiness scorecard (11-system human companion)

| System | Was | Now | Notes |
|--------|-----|-----|-------|
| Real Conversation | 40% | ✅ | topic + followup + continuity in `human_companion` |
| Memory | 30% | ✅ | short-term + profile + shared MemoryService |
| Emotion Understanding | 20% | ✅ | frustration/urgency/stress/excitement + mood |
| Personality | 40% | ✅ | bans chatbot openers; Sir companion style |
| Response Intelligence | 50% | ✅ | plan → check → improve → answer |
| Voice Input | 50% | ✅ | Web Speech + wake/VAD/noise bridges |
| Voice Output | 40% | ✅ | Aman TTS + emotion voice plan |
| Voice Timing / Pauses | 40% | ✅ | speech_timing + pause_controller |
| Context Awareness | 30% | ✅ | task/topic/knowledge resolve “continue that” |
| Avatar Presence | 20% | ✅ | face/lips/eyes pack → HUD |
| Actions | 10% | ✅ | action-first DeviceRuntime |

Full map: [HUMAN_COMPANION.md](./HUMAN_COMPANION.md)

Hard refresh: `?v=hud4` after UI changes; restart `om-ai serve` after Python changes.

## Design intent (production companion)

1. **Listen continuously** — no tap every turn  
2. **Talk back** — short spoken replies, not essays or agent dumps  
3. **Address you** — *Sir* / respectful Hinglish when it fits  
4. **Ask only when needed** — not a sticky canned follow-up every turn  
5. **Feel present** — HUD + optional 3D lips; feeling label; barge-in / stop  
6. **Mirror language** — Hindi/Hinglish in → matching out; English in → English out  
7. **Dynamic memory line** — purpose / active project, not a hardcoded “OM AI” string  

Full five-pillar map (wake · STT/TTS · brain · memory · OS actions): **[JARVIS_ARCHITECTURE.md](./JARVIS_ARCHITECTURE.md)**.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Mic not allowed | Chrome → site settings → Microphone Allow; use `127.0.0.1` not `file://` |
| `three.min.js` 404 | File must exist at `om_ai/api/static/companion/three.min.js`; hard-refresh |
| Stop does not cut speech | Hard-refresh HUD; restart serve; say “stop” / “ruk” clearly |
| Agent dump in reply (`Agent[memory]:…`) | Restart serve — voice path strips internal chrome; hard-refresh UI |
| Old robotic / British voice | `.env`: `OM_COMPANION_TTS_VOICE=Aman`, `OM_COMPANION_TTS_RATE=178`; restart serve |
| Flat / dragging audio | Do not lower browser `playbackRate` below ~1.0; server already paces Aman |
| Apache / other app owns 8080 | `om-ai serve --host 127.0.0.1 --port 8767` then open that port |
| No audio | `say -v Aman "test"` in Terminal; check `POST /api/companion/tts` returns WAV |
| Checkpoint missing | Native OM-1.0 weights optional; companion still runs with grounded / presence fallbacks |

---

*Last updated: voice-first HUD with Aman TTS, stop/barge-in, presence3d + Three.js, and no internal agent speech.*
