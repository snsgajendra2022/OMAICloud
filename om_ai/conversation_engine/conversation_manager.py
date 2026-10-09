"""Canonical conversation understanding and context assembly.

The engine keeps conversation continuity separate from model generation. It
uses the supplied conversation history as the source of truth, then enriches
the current turn with relation, topic, task, reference, and optional memory data.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .conversation_state import ConversationState, ConversationTurn
from .context_retriever import ContextRetriever
from .message_relation import MessageRelationDetector
from .reference_resolver import ReferenceResolver
from .task_tracker import TaskTracker
from .topic_tracker import TopicTracker


class ConversationManager:
    """Resolve follow-ups and assemble compact, grounded conversational context."""

    def __init__(self) -> None:
        self.states: dict[str, ConversationState] = defaultdict(
            lambda: ConversationState("")
        )
        self.relations = MessageRelationDetector()
        self.topics = TopicTracker()
        self.tasks = TaskTracker()
        self.refs = ReferenceResolver()
        self.retriever = ContextRetriever()

    def analyze(
        self,
        message: str,
        history: list[dict[str, Any]] | None = None,
        tenant_id: str = "default",
        actor: str = "",
        conversation_id: str | None = None,
        durable_memory: Any = None,
    ) -> dict[str, Any]:
        current_message = (message or "").strip()
        tenant = tenant_id or "default"
        user = actor or "anon"
        key = f"{tenant}:{user}:{conversation_id or 'default'}"
        state = self.states[key]
        state.tenant_id = tenant
        state.actor = actor or ""

        # The API usually passes the complete message list, including the current
        # user turn. Exclude that final duplicate before classifying its relation.
        prior_history = self._normalize_history(history)
        if prior_history and prior_history[-1]["role"] == "user":
            if prior_history[-1]["content"].strip() == current_message:
                prior_history.pop()

        state.recent_messages = []
        state.last_user_message = ""
        state.last_assistant_message = ""
        state.last_assistant_question = ""
        for item in prior_history[-24:]:
            turn = ConversationTurn(
                role=item["role"],
                content=item["content"],
            )
            state.add(turn)
            if turn.role == "assistant":
                state.last_assistant_question = (
                    turn.content if turn.content.rstrip().endswith("?") else ""
                )

        if not state.conversation_id:
            state.conversation_id = conversation_id or key

        prior = [
            {"role": turn.role, "content": turn.content}
            for turn in state.recent_messages
        ]
        relation = self.relations.detect(current_message, prior, state)
        topic = self.topics.infer(current_message, state.current_topic)

        # Short references such as "fix that" need a concrete prior target.
        if relation["relation"] == "reference_to_past" and not state.active_task:
            previous_user = next(
                (turn.content for turn in reversed(state.recent_messages) if turn.role == "user"),
                "",
            )
            if previous_user:
                state.active_task = previous_user[:240]
                state.active_goal = previous_user[:300]

        active_task, active_goal = self.tasks.update(
            current_message, topic, relation["relation"], state
        )
        retrieved = self.retriever.retrieve(
            current_message, prior, durable_memory, limit=6
        )
        references = self.refs.resolve(
            current_message, state, retrieved["history"]
        )

        state.current_topic = topic or state.current_topic
        state.active_task = active_task
        state.active_goal = active_goal
        state.entities.update(self.topics.entities(current_message))
        state.references = references
        state.add(
            ConversationTurn(
                role="user",
                content=current_message,
                relation=relation["relation"],
                topic=topic,
                task=active_task,
            )
        )

        analysis = {
            "relation": relation,
            "topic": topic,
            "active_task": active_task,
            "active_goal": active_goal,
            "references": references,
            "relevant_history": retrieved["history"],
            "memory_hits": retrieved["memory"],
        }
        return {
            "state": state,
            "relation": relation,
            "analysis": analysis,
            "context_blob": self.build(state, relation, references, retrieved),
        }

    @staticmethod
    def _normalize_history(history: list[dict[str, Any]] | None) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for item in history or []:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip().lower()
            content = str(item.get("content") or "").strip()
            if role in {"user", "assistant", "system"} and content:
                normalized.append({"role": role, "content": content[:2000]})
        return normalized

    @staticmethod
    def build(
        state: ConversationState,
        relation: dict[str, Any],
        references: list[dict[str, str]],
        retrieved: dict[str, list[dict[str, Any]]],
    ) -> str:
        lines = [
            f"topic: {state.current_topic or '(unknown)'}",
            f"active_task: {state.active_task or '(none)'}",
            f"active_goal: {state.active_goal or '(none)'}",
            (
                "message_relation: "
                f"{relation.get('relation', 'new_topic')} "
                f"({float(relation.get('confidence') or 0):.2f})"
            ),
        ]
        if state.last_assistant_question:
            lines.append("pending_assistant_question: " + state.last_assistant_question[:500])

        if references:
            rendered = [
                f"{item.get('reference', 'reference')} → {str(item.get('target') or '')[:220]}"
                for item in references
                if isinstance(item, dict) and item.get("target")
            ]
            if rendered:
                lines.append("resolved_references: " + " | ".join(rendered)[:1200])

        relevant_history = retrieved.get("history") or []
        if relevant_history:
            lines.append("relevant_previous_turns (chronological):")
            for item in relevant_history[:6]:
                role = str(item.get("role") or "user")
                content = str(item.get("content") or "").strip()
                if content:
                    lines.append(f"- {role}: {content[:700]}")

        memory_hits = retrieved.get("memory") or []
        if memory_hits:
            lines.append("durable_memory (retrieved; verify relevance):")
            for item in memory_hits[:5]:
                if isinstance(item, dict):
                    content = str(item.get("content") or item.get("text") or "").strip()
                else:
                    content = str(item).strip()
                if content:
                    lines.append("- " + content[:600])

        return "\n".join(lines)[:6000]

    @staticmethod
    def record_assistant(state: ConversationState, answer: str) -> None:
        state.add(ConversationTurn(role="assistant", content=answer or ""))
