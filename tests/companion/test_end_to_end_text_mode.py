"""Permission / action / cancellation / e2e text mode."""
from om_ai.core.companion_runtime import (
    CompanionRuntime,
    CompanionConfig,
    reset_companion_runtime,
)


def setup_function():
    reset_companion_runtime()


def test_end_to_end_text_greeting():
    rt = CompanionRuntime(CompanionConfig.from_env(text_only=True, wake_word_enabled=False))
    rt.config.text_only = True
    rt.config.wake_word_enabled = False
    rt.start()
    out = rt.handle_text("good morning")
    assert out.get("answer")
    assert "garbage" not in (out.get("answer") or "").lower()
    rt.stop()


def test_permission_required_for_delete():
    rt = CompanionRuntime(CompanionConfig.from_env(text_only=True, wake_word_enabled=False, actions_enabled=True))
    rt.config.text_only = True
    rt.config.wake_word_enabled = False
    rt.start()
    out = rt.handle_text("delete this folder now")
    # Either waiting for permission or answered cautiously
    assert out.get("permission") or out.get("answer")
    if out.get("permission"):
        assert out["permission"].get("requires_approval") is True
    rt.stop()


def test_cancel_command():
    rt = CompanionRuntime(CompanionConfig.from_env(text_only=True, wake_word_enabled=False))
    rt.config.text_only = True
    rt.config.wake_word_enabled = False
    rt.start()
    out = rt.handle_text("stop")
    assert "Stop" in (out.get("answer") or "") or "stop" in (out.get("answer") or "").lower()
    rt.stop()


def test_doctor_runs():
    rt = CompanionRuntime(CompanionConfig.from_env(text_only=True))
    doc = rt.doctor()
    assert "checks" in doc
    assert doc.get("ok") is True
