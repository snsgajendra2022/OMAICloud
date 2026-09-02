"""Regression: product chat UI is chat.html; tokens.html is API key admin."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "om_ai" / "api" / "static"


def test_chat_ui_exists_and_is_native_contract():
    path = STATIC / "chat.html"
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "OM" in body
    assert "/api/v1/chat/completions" in body
    assert "stripPipelineDump" in body
    assert "fetch(" in body
    assert "localStorage" in body or "session" in body.lower()
    # Date grouping (ChatGPT-style sidebar buckets)
    assert "function dayBucket" in body
    assert "Today" in body and "Yesterday" in body
    assert "Previous 7 Days" in body
    assert "appendDayGroupedChats" in body


def test_tokens_admin_ui_exists():
    path = STATIC / "tokens.html"
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "OM" in body
    assert "API" in body or "token" in body.lower() or "key" in body.lower()
