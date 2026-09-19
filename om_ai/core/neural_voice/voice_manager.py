"""STEP 105 — thin facade over voice_engine (single source of truth)."""
from __future__ import annotations

from typing import Any

from om_ai.core.voice_engine import get_voice_engine

_RT = None


class NeuralVoiceRuntime:
    """Compat runtime — all speak/plan goes through voice_engine."""

    def __init__(self) -> None:
        self.engine = get_voice_engine()

    def status(self) -> dict[str, Any]:
        st = self.engine.status()
        return {"ready": True, "step": 105, "layer": "neural_voice", **st}

    def speak_plan(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        return self.engine.speak_plan(text, emotion=emotion)

    def synthesize(self, text: str, *, emotion: str = "calm", **kwargs: Any) -> dict[str, Any]:
        return self.engine.synthesize(text, emotion=emotion, **kwargs)


def get_neural_voice() -> NeuralVoiceRuntime:
    global _RT
    if _RT is None:
        _RT = NeuralVoiceRuntime()
    return _RT
