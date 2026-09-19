"""Context awareness subsystem."""
from __future__ import annotations

from typing import Any

from .conversation_memory import ConversationMemoryCtx
from .knowledge_context import KnowledgeContext
from .task_context import TaskContext


class ContextManager:
    def __init__(self) -> None:
        self.conversation = ConversationMemoryCtx()
        self.knowledge = KnowledgeContext()
        self.task = TaskContext()

    def resolve(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        topic: str = "general",
    ) -> dict[str, Any]:
        conv = self.conversation.snapshot(history or [])
        know = self.knowledge.for_topic(topic, message)
        task = self.task.infer(message, history=history, topic=topic)
        return {
            "conversation": conv,
            "knowledge": know,
            "task": task,
            "summary": task.get("summary") or know.get("hint") or "",
        }
