"""Human context engine — meaning beyond the literal words."""
from __future__ import annotations

from typing import Any

from .conversation_analyzer import ConversationAnalyzer
from .dialogue_memory import DialogueMemory
from .implicit_meaning import ImplicitMeaning
from .incomplete_speech import IncompleteSpeech
from .relationship_state import RelationshipState
from .topic_tracker import TopicTracker


class HumanContextEngine:
    def __init__(self) -> None:
        self.analyzer = ConversationAnalyzer()
        self.implicit = ImplicitMeaning()
        self.topics = TopicTracker()
        self.relationship = RelationshipState()
        self.memory = DialogueMemory()
        self.incomplete = IncompleteSpeech()

    def understand(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        emotion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hist = history or []
        convo = self.analyzer.analyze(message, history=hist)
        topic_pack = self.topics.update(message, history=hist)
        topic = str(topic_pack.get("topic") or "general")
        rel = self.relationship.observe(
            emotion=str((emotion or {}).get("label") or "neutral"),
            turns=len(hist),
        )
        implicit = self.implicit.infer(message, conversation=convo, emotion=emotion)
        partial = self.incomplete.understand(
            message,
            history=hist,
            topic=topic,
            dialogue_blob=self.memory.blob(),
        )

        natural_ask = None
        if partial.get("incomplete"):
            natural_ask = partial.get("friend_continue")
        elif implicit.get("natural_ask"):
            natural_ask = implicit.get("natural_ask")

        system_bits = [
            "Understand unspoken meaning — do not interrogate literally.",
            str(partial.get("system_hint") or ""),
        ]
        if implicit.get("listen_first"):
            system_bits.append("Listen first. Acknowledge before advising.")
        if natural_ask:
            system_bits.append(f"A natural friend question: {natural_ask}")

        return {
            "conversation": convo,
            "topic": topic,
            "topic_pack": topic_pack,
            "relationship": rel,
            "implicit": implicit,
            "incomplete": partial,
            "natural_ask": natural_ask,
            "listen_first": bool(implicit.get("listen_first") or partial.get("incomplete")),
            "dialogue_memory": self.memory.to_dict(),
            "system_hint": " ".join(p for p in system_bits if p).strip(),
        }

    def remember_turn(self, user: str, assistant: str, *, topic: str = "") -> None:
        self.memory.remember(user, assistant, topic=topic)
