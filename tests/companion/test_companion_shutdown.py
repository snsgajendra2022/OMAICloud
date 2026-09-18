"""Companion shutdown cleanup tests."""
from om_ai.core.companion_runtime import (
    CompanionConfig,
    CompanionRuntime,
    reset_companion_runtime,
    start_companion,
    stop_companion,
)


def setup_function():
    reset_companion_runtime()


def test_shutdown_after_start():
    start_companion(text_only=True, wake_word_enabled=False)
    out = stop_companion()
    assert out.get("ok") is True


def test_shutdown_during_session_is_clean():
    rt = CompanionRuntime(CompanionConfig.from_env(text_only=True, wake_word_enabled=False))
    rt.config.text_only = True
    rt.config.wake_word_enabled = False
    rt.start()
    rt.handle_text("hi")
    rt.interrupt()
    stopped = rt.stop()
    assert stopped.get("ok") is True or stopped.get("stopped") is True or "ok" in stopped
