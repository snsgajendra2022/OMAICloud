from __future__ import annotations
from typing import Any

_EXPRESSIONS = {
    "idle": {"expression": "calm", "eyes": "soft"},
    "attentive": {"expression": "engaged", "eyes": "focused"},
    "thinking": {"expression": "thoughtful", "eyes": "soft"},
    "speaking": {"expression": "speaking", "eyes": "contact"},
    "concerned": {"expression": "soft_concern", "eyes": "gentle"},
    "excited": {"expression": "bright", "eyes": "wide"},
    "confused": {"expression": "puzzled", "eyes": "narrow"},
    "listening": {"expression": "receptive", "eyes": "focused"},
}

class FacialExpression:
    def resolve(self, presence: str) -> dict[str, Any]:
        return dict(_EXPRESSIONS.get((presence or "idle").lower(), _EXPRESSIONS["idle"]))
