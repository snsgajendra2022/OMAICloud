"""Tests for chat backend selection (OM native / OpenAI / local)."""
from __future__ import annotations

from datetime import date

import pytest

from om_ai.runtime import chat_backend as cb


def test_runtime_date_system_text_uses_calendar_date():
    text = cb.runtime_date_system_text(today=date(2026, 8, 13))
    assert "Today's date is Thursday, August 13, 2026" in text
    assert "Always treat the current year as 2026" in text
    assert "OM-1.0 native language model" in text or "OM AI" in text
    compact = cb.runtime_date_system_text_compact(today=date(2026, 8, 13))
    assert "2026-08-13" in compact
    assert "2026" in compact
    assert "OM AI" in compact
    assert len(compact) < len(text)


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


def test_default_backend_is_om_native(monkeypatch):
    monkeypatch.delenv("OM_AI_CHAT_BACKEND", raising=False)
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    assert cb.configured_backend() == "om_native"
    info = cb.resolve_backend(native_ready=True)
    assert info.backend == "om_native"
    assert info.model == "OM-1.0"


def test_auto_never_picks_ollama(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "auto")
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("OM_AI_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OM_AI_MODEL_ID", "om:free")
    info = cb.resolve_backend(local_loaded=True)
    assert info.backend == "local"
    assert info.model == "om:free"


def test_explicit_ollama_rejected(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "ollama")
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    with pytest.raises(RuntimeError, match="not part of the OM-1.0 native"):
        cb.resolve_backend(local_loaded=True)


def test_resolve_openai_when_key_and_auto(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "auto")
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OM_AI_OPENAI_MODEL", "gpt-4o-mini")
    info = cb.resolve_backend(local_loaded=False)
    assert info.backend == "openai"
    assert info.model == "gpt-4o-mini"


def test_resolve_local_fallback(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "auto")
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("OM_AI_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OM_AI_MODEL_ID", "om:free")
    info = cb.resolve_backend(local_loaded=True)
    assert info.backend == "local"
    assert info.model == "om:free"


def test_force_openai(monkeypatch):
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "openai")
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("OM_AI_OPENAI_MODEL", "gpt-4o-mini")
    info = cb.resolve_backend(local_loaded=False)
    assert info.backend == "openai"
    assert info.model == "gpt-4o-mini"
