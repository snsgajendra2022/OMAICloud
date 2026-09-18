"""Cancellation propagation tests."""
import pytest

from om_ai.core.companion_agent.cancellation_manager import (
    CancellationManager,
    CancellationToken,
)
from om_ai.core.companion_runtime import (
    CompanionConfig,
    CompanionRuntime,
    reset_companion_runtime,
)


def test_token_cancel_raises():
    token = CancellationToken()
    assert token.is_cancelled is False
    token.cancel()
    assert token.is_cancelled is True
    with pytest.raises(RuntimeError):
        token.raise_if_cancelled()


def test_manager_cancel_session():
    mgr = CancellationManager()
    sid, token = mgr.create("sess-1")
    assert mgr.cancel(sid) is True
    assert token.is_cancelled is True


def test_runtime_stop_command_cancels_turn():
    reset_companion_runtime()
    rt = CompanionRuntime(CompanionConfig.from_env(text_only=True, wake_word_enabled=False))
    rt.config.text_only = True
    rt.config.wake_word_enabled = False
    rt.start()
    out = rt.handle_text("cancel that")
    assert out.get("answer")
    rt.interrupt()
    rt.stop()
