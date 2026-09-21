"""Realtime conversation orchestrator (STEP 65)."""
from __future__ import annotations

from typing import Any, Callable

from .interruption_handler import RealtimeInterruptionHandler
from .natural_pause import NaturalPause
from .streaming_context import StreamingContext
from .turn_prediction import TurnPrediction


class RealtimeConversation:
    def __init__(self) -> None:
        self.stream = StreamingContext()
        self.predict = TurnPrediction()
        self.pause = NaturalPause()
        self.interrupt = RealtimeInterruptionHandler()

    def bind_stop(self, fn: Callable[[], None] | None) -> None:
        self.interrupt.bind(fn)

    def on_partial(self, text: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        self.pause.on_audio()
        stream = self.stream.on_partial(text)
        pred = self.predict.predict(text, history=history)
        return {**stream, **pred, "mode": "listening_continuous"}

    def on_final(self, text: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        interrupt = self.interrupt.handle(text)
        if interrupt.get("interrupted"):
            return {**interrupt, "final": text, "mode": "interrupted"}
        fin = self.stream.on_final(text)
        pred = self.predict.predict(text, history=history)
        return {**fin, **pred, **interrupt, "mode": "turn_ready"}

    def on_speaking(self, speaking: bool) -> None:
        self.interrupt.set_speaking(speaking)
