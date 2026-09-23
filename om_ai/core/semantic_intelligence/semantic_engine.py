"""Semantic engine — orchestrates full semantic understanding for a turn."""
from __future__ import annotations

from typing import Any

from .ambiguity_resolver import AmbiguityResolver
from .context_reasoner import ContextReasoner
from .conversation_state import ConversationState
from .intent_understanding import IntentUnderstanding
from .language_understanding import LanguageUnderstanding
from .meaning_representation import MeaningRepresentation
from .user_goal_detector import UserGoalDetector

_ENGINE: "SemanticEngine | None" = None


class SemanticEngine:
    """
    Raw text → structured meaning.

    Not a response generator — feeds Human Presence / Companion / Brain.
    """

    def __init__(self) -> None:
        self.language = LanguageUnderstanding()
        self.intent = IntentUnderstanding()
        self.goals = UserGoalDetector()
        self.context = ContextReasoner()
        self.ambiguity = AmbiguityResolver()
        self.meaning = MeaningRepresentation()
        self.state = ConversationState()

    def analyze(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        external_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hist = history or []
        snap = external_state or self.state.snapshot()

        lang = self.language.understand(text)
        corrected = str(lang.get("corrected") or text or "")
        locale = str(lang.get("locale") or "en")
        speech_act = str(lang.get("speech_act") or "statement")

        ctx = self.context.reason(corrected, state=snap, history=hist)
        work_text = str(ctx.get("enriched_text") or corrected)

        intent_pack = self.intent.understand(
            work_text, speech_act=speech_act, history=hist
        )
        intent = str(intent_pack.get("intent") or "conversation")

        goal_pack = self.goals.detect(
            work_text, intent=intent, speech_act=speech_act
        )
        amb = self.ambiguity.resolve(
            work_text,
            intent=intent,
            speech_act=speech_act,
            locale=locale,
        )

        listen_first = intent == "sharing" or speech_act == "share"
        polarity = "negative" if intent == "sharing" else (
            "positive" if intent in {"greeting", "thanks", "joke"} else "neutral"
        )
        topics = [str(ctx.get("topic") or "general")]
        if lang.get("entities"):
            topics = list(dict.fromkeys(topics + list(lang["entities"])[:2]))

        frame = self.meaning.build(
            text=text,
            corrected=corrected,
            intent=intent,
            goal=str(goal_pack.get("goal") or "continue"),
            speech_act=speech_act,
            entities=list(lang.get("entities") or []),
            topics=topics,
            polarity=polarity,
            confidence=float(intent_pack.get("confidence") or 0.6),
            needs_clarification=bool(amb.get("needs_clarification")),
            listen_first=listen_first,
            clarify_ask=amb.get("clarify_ask"),
            locale=locale,
            context_hint=ctx.get("hint") or "",
            goal_priority=goal_pack.get("priority"),
        )

        state_out = self.state.update(
            {
                **frame.to_dict(),
                "clarify_ask": amb.get("clarify_ask"),
            }
        )

        return {
            "text": text,
            "corrected_meaning": corrected,
            "intent": intent,
            "goal": frame.goal,
            "speech_act": speech_act,
            "confidence": frame.confidence,
            "listen_first": listen_first,
            "needs_clarification": frame.needs_clarification,
            "clarify_ask": amb.get("clarify_ask"),
            "locale": locale,
            "entities": frame.entities,
            "topics": frame.topics,
            "polarity": polarity,
            "language": lang,
            "intent_pack": intent_pack,
            "goal_pack": goal_pack,
            "context": ctx,
            "ambiguity": amb,
            "frame": frame.to_dict(),
            "state": state_out,
            "system_hint": self._hint(frame, amb, ctx),
        }

    def _hint(self, frame: Any, amb: dict[str, Any], ctx: dict[str, Any]) -> str:
        parts = [
            f"Semantic intent={frame.intent}; goal={frame.goal}; act={frame.speech_act}.",
        ]
        if frame.listen_first:
            parts.append("User is sharing — listen first, do not solve yet.")
        if amb.get("clarify_ask"):
            parts.append(f"One gentle clarify if needed: {amb['clarify_ask']}")
        if ctx.get("hint"):
            parts.append(str(ctx["hint"]))
        return " ".join(parts)


def get_semantic_engine() -> SemanticEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = SemanticEngine()
    return _ENGINE


def run_semantic(
    text: str,
    *,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return get_semantic_engine().analyze(text, history=history)
