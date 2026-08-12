"""Tests for chat backend selection (Ollama / OpenAI / local)."""
from __future__ import annotations

from om_ai.runtime import chat_backend as cb


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
