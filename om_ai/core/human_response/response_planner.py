"""Human response planner — stance before OM Brain generates language."""
from __future__ import annotations

from typing import Any

from .conversation_style import ConversationStyle
from .empathy_planner import EmpathyPlanner
from .question_strategy import QuestionStrategy
from .response_intent import ResponseIntent


class HumanResponsePlanner:
    def __init__(self) -> None:
        self.intent = ResponseIntent()
        self.empathy = EmpathyPlanner()
        self.questions = QuestionStrategy()
        self.style = ConversationStyle()

    def plan(
        self,
        *,
        timing: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
        meaning: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
        locale: str = "en",
    ) -> dict[str, Any]:
        timing = timing or {}
        emotion = emotion or {}
        meaning = meaning or {}
        action = str(timing.get("action") or "answer")
        intent = self.intent.resolve(timing_action=action, emotion=emotion, meaning=meaning)
        empathy = self.empathy.plan(emotion)
        q = self.questions.choose(
            intent=str(intent.get("intent") or ""),
            emotion=emotion,
            meaning=meaning,
            locale=locale,
        )
        style = self.style.compose(
            intent=intent,
            empathy=empathy,
            emotion=emotion,
            preferences=preferences,
        )
        return {
            "intent": intent,
            "empathy": empathy,
            "question": q,
            "style": style,
            "timing": timing,
            "speak": bool(intent.get("should_speak")),
            "wait": action == "wait",
        }
