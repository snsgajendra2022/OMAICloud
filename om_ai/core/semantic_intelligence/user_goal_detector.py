"""User goal detector — what outcome the user wants this turn."""
from __future__ import annotations

import re
from typing import Any


class UserGoalDetector:
    """Infer the underlying goal behind the utterance."""

    _GOAL_MAP = {
        "sharing": "be_heard",
        "greeting": "presence",
        "thanks": "acknowledge",
        "joke": "play",
        "research": "get_information",
        "action": "get_something_done",
        "problem": "solve_problem",
        "question": "get_answer",
        "followup": "continue_thread",
        "conversation": "social_interaction",
    }

    def detect(
        self,
        text: str,
        *,
        intent: str = "conversation",
        speech_act: str = "statement",
    ) -> dict[str, Any]:
        low = (text or "").lower()
        goal = self._GOAL_MAP.get(intent, "continue")

        if re.search(r"(?i)\b(help me|fix|solve|debug)\b", low):
            goal = "solve_problem"
        elif re.search(r"(?i)\b(explain|teach|samjha)\b", low):
            goal = "learn"
        elif re.search(r"(?i)\b(compare|vs|better|choose)\b", low):
            goal = "decide"
        elif re.search(r"(?i)\b(plan|roadmap|architecture|design)\b", low):
            goal = "plan"
        elif speech_act == "share":
            goal = "be_heard"

        return {
            "goal": goal,
            "intent": intent,
            "priority": self._priority(goal),
            "success_looks_like": self._success(goal),
        }

    def _priority(self, goal: str) -> str:
        if goal in {"be_heard", "presence"}:
            return "care_first"
        if goal in {"solve_problem", "get_something_done"}:
            return "action"
        if goal in {"get_information", "get_answer", "learn", "plan", "decide"}:
            return "intelligence"
        return "social"

    def _success(self, goal: str) -> str:
        return {
            "be_heard": "User feels acknowledged; optional gentle follow-up.",
            "presence": "Warm greeting; ready for next beat.",
            "get_information": "Clear summary without unwanted browser open.",
            "get_something_done": "Permission asked; then executed.",
            "solve_problem": "Concrete next step or fix.",
            "get_answer": "Direct, accurate answer.",
            "learn": "Clear explanation without over-explaining.",
            "plan": "Structured plan.",
            "decide": "Clear recommendation with reason.",
            "play": "Light humor, then back to user.",
            "social_interaction": "Natural companion reply.",
            "continue_thread": "Continue prior topic without restart.",
        }.get(goal, "Helpful natural reply.")
