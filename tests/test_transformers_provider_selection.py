from __future__ import annotations

import pytest

from om_ai.runtime import chat_backend


def test_transformers_provider_can_be_selected_explicitly(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "transformers")
    monkeypatch.delenv("OM_AI_CHAT_BACKEND", raising=False)
    monkeypatch.setenv("OM_HF_MODEL", "org/model-name")
    info = chat_backend.resolve_backend()
    assert info.backend == "transformers"
    assert info.model == "org/model-name"


def test_hf_alias_is_supported(monkeypatch):
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "hf")
    monkeypatch.setenv("OM_HF_MODEL", "local-model-dir")
    assert chat_backend.configured_backend() == "transformers"


def test_transformers_provider_does_not_silently_fallback(monkeypatch):
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "transformers")
    monkeypatch.delenv("OM_HF_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="OM_HF_MODEL is empty"):
        chat_backend.chat_via_transformers([{"role": "user", "content": "Hello"}])
