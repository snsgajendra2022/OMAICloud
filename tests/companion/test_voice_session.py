"""Voice session + wake word + VAD + interruption tests."""
from om_ai.core.voice_intelligence import (
    VoiceRuntime,
    WakeWordEngine,
    VoiceActivityDetector,
)
from om_ai.core.voice_intelligence.interruption_detector import InterruptionDetector
import numpy as np


def test_wake_word_detect():
    w = WakeWordEngine("hey om")
    assert w.detect_text("hey om")["detected"] is True
    assert w.detect_text("open the project")["detected"] is False


def test_vad_speech_energy():
    vad = VoiceActivityDetector(energy_threshold=0.01, start_frames=1, hangover_frames=2)
    quiet = np.zeros(512, dtype=np.float32)
    loud = np.ones(512, dtype=np.float32) * 0.2
    r1 = vad.process(quiet)
    assert r1.state == "silence"
    r2 = vad.process(loud)
    assert r2.speaking or r2.speech_started


def test_voice_session_text_only_wake_and_turn():
    rt = VoiceRuntime(text_only=True, wake_word_enabled=True)
    st = rt.start()
    assert st["ok"] is True
    wake = rt.ingest_text("hey om")
    assert wake.get("wake_only") or wake.get("ok")
    if wake.get("wake_only"):
        turn = rt.ingest_text("what can you do")
        assert turn.get("ok") is True
        assert turn.get("text")


def test_interruption_while_speaking():
    det = InterruptionDetector()
    loud = np.ones(1024, dtype=np.float32) * 0.3
    hit = det.check(loud, assistant_speaking=True)
    assert "interrupted" in hit
