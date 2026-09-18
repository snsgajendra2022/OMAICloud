"""Simple echo / feedback control while TTS is active."""
from __future__ import annotations

from typing import Any


class EchoController:
    """When TTS is speaking, raise VAD threshold to reduce self-echo triggers."""

    def __init__(self) -> None:
        self._speaking = False
        self.base_threshold = 0.015
        self.speaking_threshold = 0.05

    def set_speaking(self, speaking: bool) -> None:
        self._speaking = bool(speaking)

    def effective_threshold(self) -> float:
        return self.speaking_threshold if self._speaking else self.base_threshold

    def status(self) -> dict[str, Any]:
        return {
            "speaking": self._speaking,
            "threshold": self.effective_threshold(),
        }
