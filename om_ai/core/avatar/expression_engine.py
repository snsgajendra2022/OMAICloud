"""Expression engine adapter."""
from __future__ import annotations

from typing import Any


class ExpressionEngine:
    def map(self, emotion: str) -> dict[str, Any]:
        try:
            from om_ai.core.presence_engine.expression_engine import ExpressionEngine as EE

            return EE().map(emotion) if hasattr(EE(), "map") else {"emotion": emotion}
        except Exception:
            return {"emotion": emotion or "neutral"}
