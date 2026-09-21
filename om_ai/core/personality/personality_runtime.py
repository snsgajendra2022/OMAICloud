from __future__ import annotations

from typing import Any

from .behavior_rules import BehaviorRules
from .communication_style import CommunicationStyle
from .empathy_engine import EmpathyEngine
from .friendship_model import FriendshipModel
from .humor_engine import HumorEngine
from .identity import Identity
from .relationship_manager import RelationshipManager
from .speaking_style import SpeakingStyle

_RT = None


class PersonalityRuntime:
    def __init__(self) -> None:
        self.identity = Identity()
        self.style = SpeakingStyle()
        self.rules = BehaviorRules()
        self.humor = HumorEngine()
        self.empathy = EmpathyEngine()
        self.friendship = FriendshipModel()
        self.communication = CommunicationStyle()
        self.relationship = RelationshipManager()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "step": 102,
            "identity": self.identity.to_dict(),
            "friendship_traits": list(self.friendship.traits),
        }

    def prepare(
        self,
        message: str,
        *,
        emotion: dict[str, Any] | None = None,
        human: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        locale: str = "en",
    ) -> dict[str, Any]:
        rel = self.relationship.observe(message, profile=profile)
        friend = self.friendship.stance(emotion=emotion, human=human)
        hint = self.communication.compose_hint(
            friendship=friend,
            locale=locale,
            address=str(rel.get("address_as") or "Sir"),
        )
        return {
            "identity": self.identity.to_dict(),
            "friendship": friend,
            "relationship": rel,
            "system_hint": hint,
            "banned": list(self.communication.banned),
        }

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
