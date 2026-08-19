"""Regression: keep the product chat UI at / (tokens.html), not a conflicting embed."""
from __future__ import annotations

from pathlib import Path


def test_tokens_chat_ui_exists_and_is_native_contract():
    path = Path(__file__).resolve().parents[1] / "om_ai" / "api" / "static" / "tokens.html"
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "OM" in body
    assert "/api/v1/chat/completions" in body or "/v1/chat" in body
    assert "/api/v1/model" in body
