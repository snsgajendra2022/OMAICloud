from __future__ import annotations
from typing import Any

from .behavior_rules import BehaviorRules
from .empathy_engine import EmpathyEngine
from .humor_engine import HumorEngine
from .identity import Identity
from .speaking_style import SpeakingStyle

_RT = None

class PersonalityRuntime:
    def __init__(self) -> None:
        self.identity = Identity()
        self.style = SpeakingStyle()
        self.rules = BehaviorRules()
        self.humor = HumorEngine()
        self.empathy = EmpathyEngine()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 102, "identity": self.identity.to_dict()}

    def greet(self, user_name: str = "Gajendra") -> str:
        return f"Good morning {user_name}. I am ready."

    def style_reply(self, text: str, *, intent: str = "") -> str:
        t = self.empathy.soften(text, intent)
        return self.style.polish(t)

def get_personality() -> PersonalityRuntime:
    global _RT
    if _RT is None:
        _RT = PersonalityRuntime()
    return _RT
