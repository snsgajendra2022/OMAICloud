from om_ai.runtime.chat_pipeline import native_model_first_enabled


def test_native_model_first_defaults_on(monkeypatch):
    monkeypatch.delenv("OM_NATIVE_MODEL_FIRST", raising=False)
    assert native_model_first_enabled() is True


def test_native_model_first_can_be_disabled_explicitly(monkeypatch):
    monkeypatch.setenv("OM_NATIVE_MODEL_FIRST", "0")
    assert native_model_first_enabled() is False


def test_native_model_first_accepts_truthy_setting(monkeypatch):
    monkeypatch.setenv("OM_NATIVE_MODEL_FIRST", "1")
    assert native_model_first_enabled() is True
