"""Intent layer — delegates to chat intelligence intent understanding."""
from __future__ import annotations

from typing import Any

from om_ai.core.chat_intelligence.intent_understanding import (
    IntentResult,
    IntentUnderstanding,
)


class CompanionIntentEngine:
    def __init__(self) -> None:
        self._core = IntentUnderstanding()

    def analyze(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
    ) -> IntentResult:
        return self._core.understand(message, history=history)
