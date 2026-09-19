from __future__ import annotations
from typing import Any

from .consciousness_engine import get_consciousness


class ConsciousnessRuntime:
    """Long-running loop facade for desktop / CLI start."""

    def __init__(self) -> None:
        self.engine = get_consciousness()
        self.running = False

    def start(self) -> dict[str, Any]:
        self.running = True
        greeting = self.engine.boot_greeting()
        return {"ok": True, "running": True, "greeting": greeting, "state": self.engine.state.to_dict()}

    def stop(self) -> dict[str, Any]:
        self.running = False
        self.engine.state.mode = "idle"
        return {"ok": True, "running": False}

    def turn(self, text: str, **kwargs: Any) -> dict[str, Any]:
        return self.engine.process(text, **kwargs)
