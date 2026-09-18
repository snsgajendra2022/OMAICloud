"""Wake-word engine tests."""
from om_ai.core.voice_intelligence.wake_word_engine import WakeWordEngine


def test_default_hey_om():
    w = WakeWordEngine("hey om")
    assert w.detect_text("Hey OM, open the project")["detected"] is True


def test_configurable_phrase():
    w = WakeWordEngine("awakened om")
    assert w.detect_text("awakened om are you there")["detected"] is True
    assert w.detect_text("hey om")["detected"] is False


def test_case_insensitive():
    w = WakeWordEngine("hey om")
    assert w.detect_text("HEY OM")["detected"] is True
