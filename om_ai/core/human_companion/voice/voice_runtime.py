"""Voice runtime facade for companion platform."""
from __future__ import annotations

from typing import Any

from . import VoiceSubsystem


class VoiceRuntimeFacade:
    def __init__(self) -> None:
        self.sub = VoiceSubsystem()

    def deliver(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        return self.sub.prepare_delivery(text, emotion=emotion)
