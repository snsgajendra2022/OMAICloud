"""Companion runtime state machine tests."""
from om_ai.core.voice_intelligence.voice_state import (
    CompanionState,
    can_transition,
    assert_transition,
)


def test_listening_to_speech_detected():
    assert can_transition(CompanionState.LISTENING, CompanionState.SPEECH_DETECTED)


def test_speaking_to_interrupted():
    assert can_transition(CompanionState.SPEAKING, CompanionState.INTERRUPTED)


def test_illegal_transition_raises():
    try:
        assert_transition(CompanionState.SHUTTING_DOWN, CompanionState.SPEAKING)
        assert False, "expected ValueError"
    except ValueError:
        pass
