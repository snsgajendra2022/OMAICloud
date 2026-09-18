"""Companion startup/shutdown."""
from om_ai.core.companion_runtime import (
    start_companion,
    stop_companion,
    format_banner,
    reset_companion_runtime,
)


def setup_function():
    reset_companion_runtime()


def test_start_stop_text_only():
    status = start_companion(text_only=True, wake_word_enabled=False)
    banner = format_banner(status)
    assert "OM AI COMPANION" in banner
    assert status.get("ok") is True
    out = stop_companion()
    assert out.get("ok") is True
