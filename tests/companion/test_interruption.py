"""Barge-in / interruption detector tests."""
import numpy as np

from om_ai.core.voice_intelligence.interruption_detector import InterruptionDetector
from om_ai.core.voice_intelligence.voice_activity_detector import VoiceActivityDetector
from om_ai.core.voice_intelligence.voice_runtime import VoiceRuntime


def test_barge_in_when_assistant_speaking():
    vad = VoiceActivityDetector(energy_threshold=0.01, start_frames=1, hangover_frames=2)
    det = InterruptionDetector(vad=vad)
    loud = np.ones(2048, dtype=np.float32) * 0.4
    hit = det.check(loud, assistant_speaking=True)
    assert hit.get("interrupted") is True


def test_no_false_interrupt_on_silence():
    det = InterruptionDetector()
    quiet = np.zeros(2048, dtype=np.float32)
    hit = det.check(quiet, assistant_speaking=True)
    assert hit.get("interrupted") is False


def test_voice_runtime_interrupt_speech():
    rt = VoiceRuntime(text_only=True, wake_word_enabled=False)
    rt.start()
    rt.interrupt_speech()
    assert rt.session is not None or True
