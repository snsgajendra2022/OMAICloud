"""Tests for the optional pretrained Transformers provider (no model download needed)."""
from __future__ import annotations

import pytest

from om_ai.backends.transformers_backend import (
    TransformersBackend,
    TransformersBackendError,
)


def test_provider_fails_closed_without_model_id(monkeypatch):
    monkeypatch.delenv("OM_HF_MODEL", raising=False)
    backend = TransformersBackend()
    with pytest.raises(TransformersBackendError, match="OM_HF_MODEL"):
        backend.load()


def test_message_validation_rejects_invalid_role():
    with pytest.raises(ValueError, match="role is unsupported"):
        TransformersBackend._validate_messages([{"role": "root", "content": "hello"}])


def test_message_validation_rejects_non_string_content():
    with pytest.raises(ValueError, match="content must be a string"):
        TransformersBackend._validate_messages([{"role": "user", "content": 7}])


def test_message_validation_preserves_supported_roles():
    messages = [
        {"role": "system", "content": "Be concise"},
        {"role": "user", "content": "Hello"},
    ]
    assert TransformersBackend._validate_messages(messages) == messages


def test_unloaded_provider_reports_not_ready():
    backend = TransformersBackend()
    status = backend.health()
    assert status["ok"] is False
    assert status["provider"] == "transformers"
    assert status["parameter_count"] is None


def test_generation_rejects_empty_prompt_before_loading():
    with pytest.raises(ValueError, match="non-empty string"):
        TransformersBackend().generate("   ")
