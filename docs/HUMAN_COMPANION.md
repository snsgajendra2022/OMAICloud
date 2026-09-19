# OM Human Companion — 11 Systems

Production companion intelligence lives in `om_ai/core/human_companion/`.
It is wired into `CompanionRuntime._run_brain` on every conversational turn.

```
                 OM HUMAN COMPANION

                  Voice Input
                       |
             Conversation Intelligence
                       |
        --------------------------------
        |              |               |
     Memory        Emotion        Personality
        |              |               |
        --------------------------------
                       |
              Response Intelligence
                       |
        --------------------------------
        |                              |
      Voice                         Avatar
        |                              |
        --------------------------------
                       |
                Action System
```

## Systems & modules

| # | System | Package |
|---|--------|---------|
| 1 | Real Conversation | `conversation/` — manager, state, context_engine, dialogue_policy, topic_tracker, followup_engine |
| 2 | Memory | `memory/` — manager, short_term, user_profile (+ companion_memory episodic/semantic/working) |
| 3 | Emotion | `emotion/` — detector, mood_tracker, emotion_response, relationship_state |
| 4 | Personality | `personality/` — personality_core, behavior_rules, speaking_style, relationship_manager |
| 5 | Response IQ | `response/` — planner, answer_strategy, quality_checker, self_evaluator |
| 6–8 | Voice + Timing | `voice/` — wake, noise, vad, stt, tts, prosody, emotion_voice, speech_timing, breathing, pauses |
| 9 | Context | `context/` — context_manager, conversation_memory, knowledge_context, task_context |
| 10 | Avatar | `avatar/` — runtime, face, lip_sync, eyes, emotion_animation |
| 11 | Actions | `actions/` + DeviceRuntime (action-first in CompanionRuntime) |

## Scorecard (target architecture)

| System | Status |
|--------|--------|
| Real Conversation | ✅ |
| Memory | ✅ |
| Emotion Understanding | ✅ |
| Personality | ✅ |
| Response Intelligence | ✅ |
| Voice Input | ✅ (HUD Web Speech + wake/VAD bridges) |
| Voice Output | ✅ (Aman TTS + delivery plan) |
| Voice Timing / Pauses | ✅ |
| Context Awareness | ✅ |
| Avatar Presence | ✅ (procedural + lip plan; VRM later) |
| Actions | ✅ (action-first DeviceRuntime) |

## HUD

**http://127.0.0.1:8080/companion?v=hud4**

Restart `om-ai serve` after Python changes; hard-refresh the HUD.
