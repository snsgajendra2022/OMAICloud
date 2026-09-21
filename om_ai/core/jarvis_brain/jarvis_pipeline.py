"""
OM Jarvis Brain — STEP 51–56 human layer in front of the LLM.

User Voice/Text
  → Human Intelligence Layer
      (context, emotion, dialogue, incomplete speech, personality, relationship memory)
  → OM Brain / LLM
  → Response Intelligence
  → Voice + Avatar
"""
from __future__ import annotations

from typing import Any, Callable

from om_ai.core.human_intelligence.human_conversation_pipeline import (
    HumanConversationPipeline,
    get_human_conversation_pipeline,
)

_BRAIN: "JarvisBrain | None" = None


class JarvisBrain:
    """Facade over HumanConversationPipeline (STEP 56)."""

    def __init__(self) -> None:
        self.pipeline: HumanConversationPipeline = get_human_conversation_pipeline()
        # Expose sub-engines for callers that poke them directly
        self.human = self.pipeline.context_engine
        self.emotion = self.pipeline.emotion_engine
        self.dialogue = self.pipeline.dialogue_manager
        self.personality = self.pipeline.personality_engine
        self.wellbeing = self.pipeline.wellbeing_engine

    def perceive(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        is_action: bool = False,
        locale: str = "en",
        profile: dict[str, Any] | None = None,
        memory_blob: str = "",
        generate: Callable[..., str] | None = None,
        pre_answer: str = "",
    ) -> dict[str, Any]:
        out = self.pipeline.run(
            message,
            history=history,
            memory_blob=memory_blob,
            profile=profile,
            is_action=is_action,
            locale=locale,
            generate=generate,
            pre_answer=pre_answer,
        )
        # Compat shape for HumanCompanionPlatform
        return {
            **out,
            "pipeline": [
                "voice_input",
                "human_context_engine",
                "emotion_engine",
                "dialogue_manager",
                "memory_retrieval",
                "personality_engine",
                "llm",
                "response_optimizer",
                "voice_output",
            ],
            "emotion": out.get("emotion_pack") or {
                "emotion": out.get("emotion"),
                "label": out.get("emotion"),
                "need": out.get("need"),
                "response_style": out.get("response_style"),
                "tone": out.get("tone"),
                "followup_required": out.get("followup_required"),
            },
            "friend_move": str(
                ((out.get("dialogue") or {}).get("turn") or {}).get("action")
                or "acknowledge_and_help"
            ),
            "natural_ask": out.get("natural_ask"),
            "listen_first": out.get("listen_first"),
            "system_hint": out.get("system_hint"),
            "incomplete": out.get("incomplete") or {},
            "topic": out.get("topic"),
            "answer_seed": out.get("answer") or out.get("spoken") or "",
        }

    def remember(self, user: str, assistant: str, *, topic: str = "") -> None:
        self.pipeline.remember(user, assistant, topic=topic)


def get_jarvis_brain() -> JarvisBrain:
    global _BRAIN
    if _BRAIN is None:
        _BRAIN = JarvisBrain()
    return _BRAIN
