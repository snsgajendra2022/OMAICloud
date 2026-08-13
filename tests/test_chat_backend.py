"""Tests for chat backend selection (Ollama / OpenAI / local)."""
from __future__ import annotations

from datetime import date

from om_ai.runtime import chat_backend as cb


def test_runtime_date_system_text_uses_calendar_date():
    text = cb.runtime_date_system_text(today=date(2026, 8, 13))
    assert "Today's date is Thursday, August 13, 2026" in text
    assert "Always treat the current year as 2026" in text
    assert "Do not claim the year is 2023" in text
    assert "lack post-training" in text


def test_with_runtime_date_context_prepends_system():
    msgs = cb.with_runtime_date_context(
        [{"role": "user", "content": "What year is it?"}],
        today=date(2026, 8, 13),
    )
    assert msgs[0]["role"] == "system"
    assert "August 13, 2026" in msgs[0]["content"]
    assert "current year as 2026" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"


def test_with_runtime_date_context_merges_existing_system():
    msgs = cb.with_runtime_date_context(
        [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "hi"},
        ],
        today=date(2026, 8, 13),
    )
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"].startswith("Be concise.")
    assert "Today's date is Thursday, August 13, 2026" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"


def test_resolve_prefers_ollama_when_reachable(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "auto")
    monkeypatch.delenv("OM_AI_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OM_AI_OLLAMA_MODEL", "llama3.2")
    monkeypatch.setattr(cb, "ollama_reachable", lambda timeout=1.5: True)
    info = cb.resolve_backend(local_loaded=True)
    assert info.backend == "ollama"
    assert info.model == "llama3.2"


def test_resolve_openai_when_key_and_no_ollama(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OM_AI_OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr(cb, "ollama_reachable", lambda timeout=1.5: False)
    info = cb.resolve_backend(local_loaded=False)
    assert info.backend == "openai"
    assert info.model == "gpt-4o-mini"


def test_resolve_local_fallback(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "auto")
    monkeypatch.delenv("OM_AI_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OM_AI_MODEL_ID", "om:free")
    monkeypatch.setattr(cb, "ollama_reachable", lambda timeout=1.5: False)
    info = cb.resolve_backend(local_loaded=True)
    assert info.backend == "local"
    assert info.model == "om:free"


def test_force_openai(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "openai")
    monkeypatch.setenv("OM_AI_OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr(cb, "ollama_reachable", lambda timeout=1.5: True)
    info = cb.resolve_backend()
    assert info.backend == "openai"
