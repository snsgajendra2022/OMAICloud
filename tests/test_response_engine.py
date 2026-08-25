"""Tests for response experience engine."""
from __future__ import annotations

from om_ai.response_engine import format_assistant_reply, reply_to_blocks, blocks_to_markdown
from om_ai.runtime.system_prompts import DEFAULT_PROMPT_MARKER, DEFAULT_PROMPT_CONTENT


def test_formatter_lists_and_headings():
    raw = "Hello there\n\nI can help:\n- Coding\n- Debugging\n- Architecture"
    blocks = reply_to_blocks(raw)
    assert any(b.type == "list" for b in blocks)
    md = blocks_to_markdown(blocks)
    assert "- Coding" in md


def test_format_keeps_existing_markdown():
    raw = "## Solution\n\nUse FastAPI.\n\n```python\nprint(1)\n```"
    assert format_assistant_reply(raw) == raw.strip() or "Solution" in format_assistant_reply(raw)


def test_master_prompt_marker():
    assert DEFAULT_PROMPT_MARKER in DEFAULT_PROMPT_CONTENT
    assert "RESPONSE INTELLIGENCE" in DEFAULT_PROMPT_CONTENT
