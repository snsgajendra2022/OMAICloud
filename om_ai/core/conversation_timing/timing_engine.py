"""Timing engine — conversation manager decisions before OM speaks."""
from __future__ import annotations

from typing import Any

from .conversation_pause import ConversationPause
from .natural_interrupt import NaturalInterrupt
from .response_delay import ResponseDelay
from .thinking_time import ThinkingTime
from .turn_prediction import TurnPrediction


_ENGINE: TimingEngine | None = None


class TimingEngine:
    """
    Decide: answer | ask | wait | clarify | listen | remember | act
    before any reply generation.
    """

    def __init__(self) -> None:
        self.delay = ResponseDelay()
        self.think = ThinkingTime()
        self.predict = TurnPrediction()
        self.pause = ConversationPause()
        self.interrupt = NaturalInterrupt()

    def decide(
        self,
        meaning: dict[str, Any] | None = None,
        *,
        emotion: dict[str, Any] | None = None,
        om_speaking: bool = False,
        user_speaking: bool = False,
        stop_intent: bool = False,
    ) -> dict[str, Any]:
        meaning = meaning or {}
        emotion = emotion or {}
        label = str(emotion.get("emotion") or emotion.get("label") or "neutral")
        need = str(emotion.get("conversation_need") or emotion.get("need") or "steady")
        pred = self.predict.predict(meaning)
        intr = self.interrupt.decide(
            om_speaking=om_speaking,
            user_speaking=user_speaking,
            stop_intent=stop_intent,
        )
        if intr.get("interrupt"):
            return {
                "action": "interrupt",
                "move": "yield",
                "prediction": pred,
                "interrupt": intr,
                "delay": self.delay.plan(emotion=label, complete=True, conversation_need=need),
            }

        if meaning.get("needs_listening") or pred.get("om_should_hold"):
            hold = self.pause.begin_hold(str(meaning.get("text") or ""))
            return {
                "action": "wait",
                "move": "listen",
                "reason": "incomplete_or_continuing",
                "prediction": pred,
                "hold": hold,
                "delay": self.delay.plan(
                    emotion=label,
                    complete=False,
                    conversation_need=need,
                    word_count=int((meaning.get("completion") or {}).get("word_count") or 0),
                ),
            }

        goal = str(meaning.get("inferred_goal") or "express")
        if need in {"listen_first", "support_and_listen"}:
            action = "ask" if label in {"sad", "stressed", "frustrated", "tired"} else "comfort"
            move = "empathize_then_invite"
        elif goal == "act":
            action, move = "act", "plan_then_do"
        elif goal == "ask":
            action, move = "answer", "direct_answer"
        elif meaning.get("missing_information") and not meaning.get("finished_enough"):
            action, move = "clarify", "one_gentle_question"
        else:
            action, move = "answer", "natural_reply"

        complexity = "heavy" if goal == "act" else ("light" if len(str(meaning.get("text") or "").split()) < 6 else "normal")
        return {
            "action": action,
            "move": move,
            "reason": goal,
            "prediction": pred,
            "interrupt": intr,
            "think": self.think.budget(complexity=complexity, emotion=label),
            "delay": self.delay.plan(
                emotion=label,
                complete=bool(meaning.get("finished_enough", True)),
                conversation_need=need,
                word_count=int((meaning.get("completion") or {}).get("word_count") or 0),
            ),
            "should_answer": action in {"answer", "ask", "comfort", "act", "clarify"},
            "should_wait": action == "wait",
        }


def get_timing_engine() -> TimingEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = TimingEngine()
    return _ENGINE
