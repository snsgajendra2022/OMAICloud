"""Predict intent from partial speech — never wait for perfection."""
from __future__ import annotations

import re
from typing import Any


class TurnPrediction:
    def predict(self, partial: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        low = (partial or "").lower().strip()
        hist = history or []
        intent = "continue"
        confidence = 0.4
        if re.search(r"(?i)\b(open|launch|start|close|kill)\b", low):
            intent, confidence = "action", 0.7
        elif re.search(r"(?i)\b(what|why|how|kya|kaise)\b", low) or "?" in low:
            intent, confidence = "question", 0.65
        elif re.search(r"(?i)\b(tired|stress|difficult|exhausted)\b", low):
            intent, confidence = "emotion_share", 0.7
        elif re.search(r"(?i)\b(remember|prefer|my name)\b", low):
            intent, confidence = "memory", 0.75
        elif re.search(r"(?:\.\.\.|…|\bbut\s*)$", low):
            intent, confidence = "partial_story", 0.8
        elif hist and len(low.split()) <= 4:
            intent, confidence = "followup", 0.55
        return {
            "predicted_intent": intent,
            "confidence": confidence,
            "can_prefetch": confidence >= 0.7 and intent in {"action", "question"},
        }
