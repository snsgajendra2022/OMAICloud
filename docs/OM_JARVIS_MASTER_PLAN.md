# OM AI — Jarvis-Class Personal AI Companion (Master Plan)

Target: **Tony Stark → JARVIS → OM AI** via engineering layers, not fiction.

```
Human Presence + Intelligence + Memory + Voice + Vision
+ Actions + Personality + Avatar + Autonomy
```

Current baseline before STEPs 100–112 was ~voice + LLM + orb + TTS (~20–30%).  
This pass scaffolds the **complete system architecture** and wires it into Companion OS.

---

## Final UX (`om-ai start`)

```
================================================
                    OM AI
              [3D HUMAN AVATAR]
                 Listening
"Good morning Gajendra. I am ready."
------------------------------------------------
Memory: You are working on OM AI
Activity:
✓ Voice activated
✓ Understanding request
✓ Checking memory
================================================
```

---

## Steps 100–112

| Step | Package | Role |
|------|---------|------|
| 100 | `om_ai/core/om_consciousness/` | Central brain: understand → decide → plan → act → learn |
| 101 | `om_ai/core/human_dialogue/` | Natural conversation (bad day / tired ≠ FAQ) |
| 102 | `om_ai/core/personality/` | Identity, style, empathy, humor rules |
| 103 | `om_ai/core/human_memory/` (+ semantic + memory_engine) | Human-like memory |
| 104 | `om_ai/core/presence_engine/` (+ expression/tone) | LISTENING / THINKING / CONCERNED… |
| 105 | `om_ai/core/neural_voice/` | Neural TTS facade (ElevenLabs when keyed) |
| 106 | `om_ai/om_avatar/` | 3D avatar runtime → Presence3D / Unity / Unreal |
| 107 | `om_ai/core/vision/` (+ vision_engine) | Eyes — screen/camera (permission-gated) |
| 108 | `om_ai/core/action_engine/` | Goal → plan → verify (e.g. response-quality diagnosis) |
| 109 | `om_ai/core/autonomous_agent/` (+ agent_loop, task_graph…) | Goal loop |
| 110 | `om_ai/core/live_presence/` | Event bus + activity stream |
| 111 | `om_desktop/` | Electron desktop shell scaffold |
| 112 | Companion OS + `om-ai start` | Wired experience |

---

## Architecture

```
                  OM AI
                 3D AVATAR
                     |
              HUMAN PRESENCE
                     |
              CONSCIOUSNESS
                     |
 ------------------------------------------------
 Memory · Personality · Reasoning · Knowledge
 Vision · Planning · Agents · Dialogue
 ------------------------------------------------
                     |
                  ACTIONS
                     |
          Computer / Apps / Internet
```

---

## What is live vs external

| Live in this repo | Still external / paid |
|-------------------|------------------------|
| Consciousness routing + activity stream | MetaHuman / Unreal body |
| Human dialogue + personality polish | ElevenLabs butler clone keys |
| Action plans (“3 possible issues…”) | True screen vision (OS permission) |
| Web Three.js full-body presence | Electron packaging polish |
| `om-ai start` → companion UI | Projector desk HUD |

---

## Commands

```bash
om-ai start
# → boots consciousness greeting + companion UI
# → http://127.0.0.1:8767/companion

om-ai companion status
```

Neural voice:

```bash
OM_NEURAL_TTS_PROVIDER=elevenlabs
OM_NEURAL_TTS_API_KEY=...
OM_NEURAL_TTS_VOICE_ID=...
```

---

## Honest bottom line

OM is no longer “orb + TTS only” in architecture.  
Jarvis *feeling* still scales with **neural voice + MetaHuman/VRM body + long-term memory + real actions** — those are the next materials on top of this OS.
