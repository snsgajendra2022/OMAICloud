# OM Jarvis Architecture — Five Pillars (Production Map)

This is how the classic “Jarvis” stack maps onto **OM Companion** — not a toy
`while True: listen → speak` script. The production spine is FastAPI +
`CompanionRuntime` + Companion Brain + DeviceRuntime.

**HUD:** `http://127.0.0.1:8080/companion?v=hud4`  
**Details:** [COMPANION_PAGE.md](./COMPANION_PAGE.md) · Voice: [JARVIS_VOICE.md](./JARVIS_VOICE.md)

---

## Production readiness (honest)

| System | Status |
|--------|--------|
| HUD UI | ✅ ~90% |
| Voice input | ✅ ~75% |
| Voice output | ✅ ~70% |
| Brain | ✅ ~75% |
| Memory | ✅ ~85% |
| Personality | ✅ ~80% |
| Avatar | ✅ ~65% (procedural; VRM later) |
| Actions | ✅ ~75% |
| Real conversation | ✅ ~75% |

Cross-cutting: one `session_id` + `user_key`, shared MemoryService, action-first DeviceRuntime + live weather, personality finalize, avatar lips + WS reconnect.

## Living companion (STEP 64–70)

Do **not** add more duplicate intelligence brains. Wire presence + realtime + tools:

```
Presence Runtime
  → Human Conversation Layer (emotion/memory/personality/reasoning)
  → Capability / Tool System
  → Permission + Security
  → Voice + Avatar + Vision
  → OM Companion (HUD / desktop app)
```

| Step | Package |
|------|---------|
| 64 Presence | `om_ai/core/presence_runtime/` |
| 65 Realtime convo | `om_ai/core/conversation_runtime/` (`realtime_*`, `conversation_loop`) |
| 66 Multimodal | `om_ai/core/multimodal_intelligence/` |
| 67 Capabilities | `om_ai/core/capability_system/` |
| 68 Self-improve | `om_ai/core/self_improvement/` (offline only) |
| 69 Desktop shell | `om_companion_app/` (Tauri + React) |
| 70 Tests | `tests/test_step70_integration.py` |

All wired into `CompanionRuntime` — restart `om-ai serve` and use `/companion`.

---

## Pillar map

| Pillar | Classic toy example | OM production |
|--------|---------------------|---------------|
| **1. Wake word** | `if "jarvis" in command` (full STT always on) | Lightweight local phrase gate + optional Picovoice Porcupine |
| **2. STT / TTS** | `speech_recognition` + `pyttsx3` | Browser Web Speech (HUD) or local STT; TTS = Aman/`say` or ElevenLabs |
| **3. LLM / Brain** | GPT-4 / Gemini / Ollama call | OM Companion Brain + HumanCompanionPlatform friend pipeline (meaning → emotion → memory → FriendMind → respond → voice) |
| **4. Memory** | `chat_history[]` + SQLite | Session history (short-term) + `artifacts/companion/memory.json` + human_memory |
| **5. Intent / OS** | `if "youtube"` … `os`/`subprocess` | `_plan_action` → DeviceRuntime capabilities (browser, apps, volume, files) |

---

## 1. Wake Word (always ready, not always heavy)

**Goal:** Stay ready without burning CPU on a full LLM every ambient second.

| Mode | When | Module |
|------|------|--------|
| **HUD** | Always-listening Web Speech in the browser | `om_ai/api/static/companion/index.html` — wake can be off; you just speak |
| **Local phrase** | Transcript contains `hey om` / `jarvis` / aliases | `om_ai/core/voice_intelligence/wake_word_engine.py` |
| **Porcupine (optional)** | Ultra-light always-on mic | Same engine if `OM_WAKE_PORCUPINE_KEY` + `pvporcupine` installed |

```bash
# Optional Porcupine
export OM_WAKE_PORCUPINE_KEY=your_picovoice_key
export OM_WAKE_PORCUPINE_KEYWORD=jarvis   # or porcupine built-in keyword
export OM_COMPANION_WAKE_WORD="hey om"    # primary phrase; aliases include jarvis
```

After wake-only (“Jarvis” with no command), OM answers: **“Ji sir, kahiye?”**

---

## 2. Speech-to-Text & Text-to-Speech

### STT (listen)

| Path | Tech |
|------|------|
| Companion HUD | Browser Web Speech API (`en-IN` / `hi-IN`) → `POST /api/companion/message` |
| Native / CLI | VoiceRuntime STT → `on_final_transcript` → brain |
| Upload | `POST /api/companion/hear` |

### TTS (speak)

| Provider | Env | Notes |
|----------|-----|--------|
| macOS `say` (default) | `OM_COMPANION_TTS_PROVIDER=macos` | Voice **Aman**, rate **178** |
| ElevenLabs | `OM_COMPANION_TTS_PROVIDER=elevenlabs` + API key | Neural; see JARVIS_VOICE.md |
| Soft fallbacks | — | Never dump robotic internal chrome |

Client plays WAV from `POST /api/companion/tts` with lip-sync plan.

---

## 3. Brain / LLM

```
User text
  → CompanionRuntime.handle_text
  → Companion Brain (semantic understanding + response strategy)
  → strip internal chrome / shape for speech
  → optional DeviceRuntime action
  → CompanionOS enrich (presence, memory line, avatar)
  → spoken reply
```

OM uses the **in-repo companion brain**, not a hard-coded GPT-only loop. Cloud or local LLM backends can sit behind the brain when configured; the companion contract stays the same.

---

## 4. Memory

| Layer | What | Where |
|-------|------|--------|
| **Short-term** | Current session turns | `VoiceSession.history` (dynamic chat history) |
| **Working / episodic** | Per-turn store | `MemoryService.remember_turn(...)` → `artifacts/companion/memory.json` |
| **Long-term prefs** | Name, likes | `remember_fact` / preference memory (+ human_memory JSONL) |

Turns are written with proper kwargs (`session_key`, `user_key`, `role`, `content`) so history actually persists.

---

## 5. Intent automation & OS control

Function-calling style: natural language → `_plan_action` → capability invoke.

| Intent examples | Capability |
|-----------------|------------|
| “YouTube kholo” / play X on YouTube | `browser.open` |
| “Mausam kaisa hai” / weather | `browser.open` (live search) |
| “Volume badhao” / mute | `system.volume` |
| “Open VS Code” / project folder | `application.open` |
| List / delete files | `filesystem.*` (destructive needs approval) |

Controllers live under `om_ai/core/device_runtime/` (`BrowserController`, `SystemController`, …).  
Risky actions go through the permission gate (“Say yes to allow”).

---

## Why not the toy `while True` loop?

```python
# Educational sketch only — NOT how OM runs in production
while True:
    command = listen_command()
    if "jarvis" in command:
        speak("Ji sir, kahiye?")
        execute_task(listen_command())
```

That pattern blocks one process, mixes wake+STT+brain+OS in one file, and fights the browser HUD.

OM instead:

1. **Serve** HTTP/WebSocket (`om-ai serve`)
2. **HUD or native voice** feeds text into `CompanionRuntime`
3. **Wake** is a cheap gate (or browser always-listen)
4. **Brain + memory + devices** are separate modules with one lifecycle

---

## Quick env checklist

```bash
OM_COMPANION_ENABLED=1
OM_COMPANION_WAKE_WORD_ENABLED=1
OM_COMPANION_WAKE_WORD=hey om
OM_COMPANION_TTS_PROVIDER=macos
OM_COMPANION_TTS_VOICE=Aman
OM_COMPANION_TTS_RATE=178
OM_COMPANION_MEMORY=1
OM_COMPANION_ACTIONS_ENABLED=1
# Optional:
# OM_WAKE_PORCUPINE_KEY=...
# OM_COMPANION_TTS_PROVIDER=elevenlabs
```

---

## Key source files

```
om_ai/core/companion_runtime/companion_runtime.py   # lifecycle + handle_text + actions
om_ai/core/companion_brain/                         # LLM/semantic brain
om_ai/core/companion_memory/memory_service.py       # short + long memory
om_ai/core/voice_intelligence/wake_word_engine.py   # wake / Porcupine hook
om_ai/core/voice_intelligence/voice_runtime.py      # STT session + wake strip
om_ai/core/device_runtime/                          # OS / browser / volume
om_ai/core/voice_engine/                            # TTS providers
om_ai/api/companion/routes.py                       # HTTP API
om_ai/api/static/companion/index.html               # Jarvis HUD
```
