# Real-Time Human Conversation Intelligence

OM is not a voice chatbot (STT → LLM → reply).

It runs a **Human Conversation Loop**:

```
User Voice
  → Audio Intelligence (VAD / noise / barge-in)
  → Speech Intelligence (partial / incomplete / meaning)
  → Emotional Intelligence (text + context + voice cues)
  → Conversation Timing (answer | wait | ask | listen | act)
  → Human Response Planner (stance before words)
  → OM Brain / Friend / Actions
  → TTS + Avatar
```

## Packages

| Package | Role |
|---------|------|
| `om_ai/core/audio_intelligence/` | Listening quality, VAD, segments, barge-in |
| `om_ai/core/speech_intelligence/` | Incomplete speech, uncertainty, meaning |
| `om_ai/core/conversation_timing/` | When to wait vs answer |
| `om_ai/core/emotional_intelligence/` | Facade over emotion_intelligence + voice cues |
| `om_ai/core/human_response/` | Intent / empathy / question / style plan |
| `om_ai/core/human_conversation_intelligence/` | Master orchestrator |

## API

- `POST /api/companion/partial` — interim speech (no answer)
- `POST /api/companion/message` — final turn; returns `hold: true` when incomplete
- `force_commit: true` — commit after natural pause

## Browser companion

`om_ai/api/static/companion/index.html` sends partials, holds incomplete finals ~950ms, then force-commits; barge-in calls `/interrupt`.

## Test

```bash
.venv/bin/python -m pytest tests/test_human_conversation_intelligence.py -q
```
