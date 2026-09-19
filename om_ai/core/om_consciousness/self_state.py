from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SelfState:
    """OM's internal self-model — who I am, what I'm doing, what I know about the user."""

    name: str = "OM"
    mode: str = "idle"  # idle|listening|thinking|speaking|acting
    focus: str = ""
    user_name: str = "Gajendra"
    relationship: str = "personal_ai_assistant"
    last_goal: str = ""
    activity: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mode": self.mode,
            "focus": self.focus,
            "user_name": self.user_name,
            "relationship": self.relationship,
            "last_goal": self.last_goal,
            "activity": list(self.activity[-12:]),
        }
