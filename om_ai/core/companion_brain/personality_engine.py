"""Thin bridge to companion_personality from companion_brain."""
from __future__ import annotations

from typing import Any

from om_ai.core.companion_personality import CompanionPersonalityEngine


class PersonalityBridge:
    def __init__(self) -> None:
        self._engine = CompanionPersonalityEngine()

    def prepare(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._engine.prepare(*args, **kwargs)

    def finalize(self, answer: str, pack: dict[str, Any], **kwargs: Any) -> str:
        return self._engine.finalize(answer, pack, **kwargs)

    @property
    def expression(self):
        return self._engine.expression
