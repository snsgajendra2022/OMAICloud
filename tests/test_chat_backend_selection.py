from om_ai.runtime.chat_backend import configured_backend


def test_explicit_openai_chat_backend_overrides_stale_native_provider(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "openai")
    assert configured_backend() == "openai"


def test_explicit_native_chat_backend_remains_native(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "om_native")
    assert configured_backend() == "om_native"


def test_auto_selects_cloud_when_key_is_configured(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "auto")
    monkeypatch.setenv("OM_AI_OPENAI_API_KEY", "test-only-key")
    assert configured_backend() == "openai"
