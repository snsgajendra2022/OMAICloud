"""Dialogue manager — plan the conversational move."""
from __future__ import annotations

from typing import Any

from .conversation_goal import ConversationGoal
from .followup_generator import FollowupGenerator
from .interruption_handler import InterruptionHandler
from .question_generator import QuestionGenerator
from .turn_manager import TurnManager


class DialogueManager:
    def __init__(self) -> None:
        self.goals = ConversationGoal()
        self.turns = TurnManager()
        self.followups = FollowupGenerator()
        self.questions = QuestionGenerator()
        self.interruptions = InterruptionHandler()

    def plan(
        self,
        message: str,
        *,
        human: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
        is_action: bool = False,
        locale: str = "en",
    ) -> dict[str, Any]:
        interrupt = self.interruptions.assess(message)
        goal = self.goals.infer(
            message, human=human, emotion=emotion, is_action=is_action
        )
        turn = self.turns.decide(goal, interrupted=bool(interrupt.get("interrupted")))
        ask = self.questions.generate(human=human, emotion=emotion, locale=locale)
        follow = self.followups.maybe(message, human=human, turn=turn)

        mode = str(turn.get("move") or "answer")
        hint_parts = [
            f"Conversation move: {mode} ({turn.get('action')}).",
            f"Goal: {goal.get('goal')}.",
        ]
        if mode == "listen":
            hint_parts.append("Acknowledge first. Do not jump to solutions.")
        if ask and mode in {"listen", "ask", "encourage"}:
            hint_parts.append(f"One natural question if needed: {ask}")

        return {
            "goal": goal,
            "turn": turn,
            "interrupt": interrupt,
            "question": ask,
            "followup": follow,
            "mode": mode,
            "system_hint": " ".join(hint_parts),
        }
