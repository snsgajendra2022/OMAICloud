from __future__ import annotations

import pytest

from om_ai.runtime import chat_backend


def test_vllm_provider_can_be_selected_and_reports_model(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "vllm")
    monkeypatch.delenv("OM_AI_CHAT_BACKEND", raising=False)
    monkeypatch.setenv("OM_VLLM_MODEL", "org/licensed-model")
    info = chat_backend.resolve_backend()
    assert info.backend == "vllm"
    assert info.model == "org/licensed-model"


def test_vllm_alias_is_supported(monkeypatch):
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "self_hosted")
    assert chat_backend.configured_backend() == "vllm"


def test_vllm_missing_model_fails_closed(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "vllm")
    monkeypatch.delenv("OM_VLLM_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="OM_VLLM_MODEL is empty"):
        chat_backend.chat_via_vllm([{"role": "user", "content": "Hello"}])


def test_vllm_chat_calls_openai_compatible_endpoint(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "A real model answer"}}]}

    class Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json, headers):
            assert url == "http://inference:8000/v1/chat/completions"
            assert json["model"] == "org/licensed-model"
            assert json["messages"][-1]["content"] == "Hello"
            assert headers["Authorization"] == "Bearer test-secret"
            return Response()

    monkeypatch.setenv("OM_VLLM_BASE_URL", "http://inference:8000/v1")
    monkeypatch.setenv("OM_VLLM_MODEL", "org/licensed-model")
    monkeypatch.setenv("OM_VLLM_API_KEY", "test-secret")
    monkeypatch.setattr(chat_backend.httpx, "Client", Client)
    answer = chat_backend.chat_via_vllm([{"role": "user", "content": "Hello"}])
    assert answer == "A real model answer"
