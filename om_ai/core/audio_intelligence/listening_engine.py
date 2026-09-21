"""Listening engine — unifies VAD, quality, segmenting for the companion loop."""
from __future__ import annotations

from typing import Any

from .conversation_audio import ConversationAudio
from .speech_segmenter import SpeechSegmenter


_ENGINE: ListeningEngine | None = None


class ListeningEngine:
    def __init__(self) -> None:
        self.audio = ConversationAudio()
        self.segments = SpeechSegmenter()
        self._last: dict[str, Any] = {}

    def on_audio(self, *, rms: float = 0.0, speech_prob: float = 0.0) -> dict[str, Any]:
        pack = self.audio.observe(rms=rms, speech_prob=speech_prob)
        self._last = pack
        return pack

    def on_partial_text(self, text: str) -> dict[str, Any]:
        seg = self.segments.push_partial(text)
        return {**self._last, "segment": seg}

    def on_final_text(self, text: str) -> dict[str, Any]:
        seg = self.segments.commit(text)
        return {**self._last, "segment": seg}

    def set_om_speaking(self, speaking: bool) -> None:
        self.audio.set_om_speaking(speaking)

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "om_speaking": self.audio.om_speaking,
            "last": self._last,
        }


def get_listening_engine() -> ListeningEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = ListeningEngine()
    return _ENGINE
