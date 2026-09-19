"""Conversation manager — owns continuous dialogue across turns."""
from __future__ import annotations

from typing import Any

from .conversation_state import ConversationState
from .context_engine import ContextEngine
from .dialogue_policy import DialoguePolicy
from .followup_engine import FollowupEngine
from .topic_tracker import TopicTracker


class ConversationManager:
    def __init__(self) -> None:
        self.state = ConversationState()
        self.topics = TopicTracker()
        self.followups = FollowupEngine()
        self.context = ContextEngine()
        self.policy = DialoguePolicy()

    def prepare(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        memory_blob: str = "",
        emotion: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        semantic: dict[str, Any] | None = None,
        is_action: bool = False,
        task: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        topic_pack = self.topics.update(message, history=history)
        self.state.active_topic = topic_pack["topic"]
        follow = self.followups.analyze(
            message,
            state=self.state.to_dict(),
            topic=self.state.active_topic,
            last_assistant=self.state.last_assistant,
            last_user=self.state.last_user,
        )
        if follow.get("resolved_reference"):
            self.state.pending_reference = str(follow["resolved_reference"])
        ctx = self.context.build(
            message,
            history=history,
            topic=self.state.active_topic,
            memory_blob=memory_blob,
            emotion=emotion,
            profile=profile,
            followup=follow,
            task=task,
        )
        pol = self.policy.decide(
            semantic=semantic,
            emotion=emotion,
            followup=follow,
            is_action=is_action,
        )
        return {
            "state": self.state.to_dict(),
            "topic": topic_pack,
            "followup": follow,
            "context": ctx,
            "policy": pol,
            "enriched_message": self._enrich_message(message, follow),
        }

    def _enrich_message(self, message: str, follow: dict[str, Any]) -> str:
        if follow.get("is_reference") and follow.get("resolved_reference"):
            return f"{message}\n\n[Context: continuing — {follow['resolved_reference'][:180]}]"
        return message

    def commit(self, user: str, assistant: str) -> None:
        self.state.bump(user, assistant)
