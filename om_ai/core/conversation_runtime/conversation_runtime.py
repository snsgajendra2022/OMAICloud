"""STEP 52 continuous conversation orchestrator."""
from __future__ import annotations

from typing import Any

from .context_window import ContextWindow
from .conversational_flow import ConversationalFlow
from .dialogue_memory import DialogueMemory
from .interruption_manager import InterruptionManager
from .response_timing import ResponseTiming
from .turn_manager import TurnManager


class ConversationRuntime:
    def __init__(self) -> None:
        self.turns = TurnManager()
        self.interruptions = InterruptionManager()
        self.window = ContextWindow()
        self.dialogue = DialogueMemory()
        self.flow = ConversationalFlow()
        self.timing = ResponseTiming()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "step": 52,
            "name": "Human Conversation Runtime",
            "topic": self.window.topic,
            "turns": len(self.turns.turns),
        }

    def on_user(self, text: str, *, speaking: bool = False) -> dict[str, Any]:
        inter = self.interruptions.analyze(text, speaking=speaking)
        if inter.get("should_stop_speech"):
            self.turns.mark_interrupted()
        topic = self.flow.infer_topic(text)
        self.window.set_topic(topic)
        turn = self.turns.begin_user(text, topic=topic)
        self.dialogue.remember("user", text)
        return {
            "turn": turn.to_dict(),
            "interrupt": inter,
            "topic": topic,
            "context": self.window.to_dict(),
            "timing": self.timing.plan(presence_mode="attentive", text_len=len(text or "")),
        }

    def on_assistant(self, text: str, *, user_text: str = "", presence_mode: str = "speaking") -> dict[str, Any]:
        topic = self.window.topic or self.flow.infer_topic(user_text)
        follow = self.flow.follow_up(user_text, text, topic=topic)
        spoken = self.flow.merge_follow_up(text, follow)
        turn = self.turns.begin_assistant(spoken, topic=topic)
        self.dialogue.remember("assistant", spoken)
        if follow:
            self.window.add_question(follow)
        return {
            "turn": turn.to_dict(),
            "answer": spoken,
            "follow_up": follow,
            "timing": self.timing.plan(presence_mode=presence_mode, text_len=len(spoken)),
            "history": self.turns.history(12),
            "context_blob": self.window.blob(self.turns.history(12)),
        }
