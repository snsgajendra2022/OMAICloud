# OM AI Response Experience Layer

ChatGPT/JARVIS-style presentation is **not** only model size.

```text
OM Model → Reasoning → Memory → Response Experience Engine → Streaming UI
```

## In this repo

| Piece | Path |
|-------|------|
| Master prompt | `[OM-RX-v1]` in `om_ai/runtime/system_prompts.py` |
| Response engine | `om_ai/response_engine/` |
| Streaming chat | `/api/v1/chat/completions` + `chat.html` |
| Markdown UI | `renderMarkdown()` in `om_ai/api/static/chat.html` |

## Engine modules

- `formatter.py` — blocks + structured markdown
- `markdown_parser.py` — safe HTML helper
- `emotion_style.py` — openings / experience phases
- `stream_manager.py` — progressive chunk helpers

Restart `om-ai serve` after changes so the new system prompt loads.
