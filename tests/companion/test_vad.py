"""Voice activity detection tests."""
import numpy as np

from om_ai.core.voice_intelligence.voice_activity_detector import VoiceActivityDetector


def test_silence_then_speech_then_end():
    vad = VoiceActivityDetector(energy_threshold=0.01, start_frames=1, hangover_frames=2)
    quiet = np.zeros(512, dtype=np.float32)
    loud = np.ones(512, dtype=np.float32) * 0.25

    assert vad.process(quiet).state == "silence"
    started = vad.process(loud)
    assert started.speech_started or started.speaking
    ongoing = vad.process(loud)
    assert ongoing.speaking or ongoing.state in {"speech", "speech_ongoing", "speaking"}
    # hangover ends speech
    ended = None
    for _ in range(5):
        ended = vad.process(quiet)
    assert ended is not None
    assert ended.speech_ended or ended.state == "silence"
