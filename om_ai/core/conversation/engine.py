"""Lightweight, deterministic conversation context preparation.

This layer does not generate answers. It preserves task continuity and prepares a
compact, relevant context for the single configured ModelGateway/backend.
It deliberately avoids phrase-to-answer mappings.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class MessageRelation(str, Enum):
    NEW_TOPIC = "NEW_TOPIC"
    CONTINUATION = "CONTINUATION"
    FOLLOW_UP = "FOLLOW_UP"
    ANSWER = "ANSWER"
    CLARIFICATION = "CLARIFICATION"
    CORRECTION = "CORRECTION"
    CONFIRMATION = "CONFIRMATION"
    REJECTION = "REJECTION"
    REFERENCE = "REFERENCE"
    EXPANSION = "EXPANSION"
    CONSTRAINT_UPDATE = "CONSTRAINT_UPDATE"
    ACTION_REQUEST = "ACTION_REQUEST"
    TOPIC_SWITCH = "TOPIC_SWITCH"


@dataclass
class ConversationState:
    conversation_id: str = ""
    current_topic: str = ""
    previous_topic: str = ""
    active_task: str = ""
    active_goal: str = ""
    current_intent: str = ""
    previous_intent: str = ""
    last_user_message: str = ""
    last_assistant_message: str = ""
    pending_question: str = ""
    unresolved_questions: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    references: list[dict[str, Any]] = field(default_factory=list)
    recent_messages: list[dict[str, str]] = field(default_factory=list)
    relevant_history: list[dict[str, str]] = field(default_factory=list)
    summary: str = ""
    task_status: str = "idle"
    confidence: float = 0.0
    relation: MessageRelation = MessageRelation.NEW_TOPIC


_WORD_RE = re.compile(r"[A-Za-z0-9_+#.-]{2,}|[\u0900-\u097F]{2,}")
_REFERENCE_RE = re.compile(
    r"\b(it|this|that|them|these|those|same|above|previous|earlier|before|again|"
    r"the issue|the file|the code|the error|that error|this problem|continue|next)\b",
    re.IGNORECASE,
)
_AFFIRM = {"yes", "yeah", "yep", "ok", "okay", "sure", "correct", "right", "done", "i checked"}
_NEGATIVE = {"no", "nope", "not yet", "still broken", "doesn't work", "did not work"}
_CORRECTION_STARTS = ("actually", "correction", "i meant", "not ", "instead", "wrong", "that's not")
_ACTION_STARTS = ("fix ", "implement ", "update ", "create ", "write ", "change ", "remove ", "add ")


_STOP_WORDS = {
    "the", "and", "for", "with", "you", "your", "are", "was", "were", "from",
    "have", "has", "had", "this", "that", "these", "those", "then", "than",
    "what", "when", "where", "which", "how", "can", "could", "would", "should",
    "please", "about", "into", "onto", "there", "here", "not", "but", "all",
}


def _words(text: str) -> set[str]:
    return {
        w.lower() for w in _WORD_RE.findall(text or "")
        if len(w) > 2 and w.lower() not in _STOP_WORDS
    }


def _content(message: dict[str, Any]) -> str:
    value = message.get("content", "")
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(x.get("text") or "") if isinstance(x, dict) else str(x) for x in value).strip()
    return str(value or "").strip()


def _normalise(messages: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user").strip().lower()
        if role not in {"system", "user", "assistant"}:
            continue
        content = _content(message)
        if content:
            result.append({"role": role, "content": content})
    return result


def _is_question(text: str) -> bool:
    tail = (text or "").strip().splitlines()[-1:] or [""]
    return "?" in tail[0] or bool(re.search(r"\b(what|which|where|when|why|how|could you|can you|please share)\b", tail[0], re.I))


def _overlap(a: str, b: str) -> float:
    aw, bw = _words(a), _words(b)
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / max(1, len(aw | bw))


def classify_relation(current: str, history: list[dict[str, str]]) -> MessageRelation:
    """Infer relation from conversational position and content signals."""
    text = (current or "").strip()
    low = re.sub(r"\s+", " ", text.lower()).strip(" .!?")
    if not history:
        return MessageRelation.NEW_TOPIC
    previous = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")
    previous_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    if any(low.startswith(prefix) for prefix in _CORRECTION_STARTS):
        return MessageRelation.CORRECTION
    if low in _AFFIRM or low.startswith(("yes, ", "okay, ", "done, ", "i checked")):
        return MessageRelation.ANSWER if _is_question(previous) else MessageRelation.CONFIRMATION
    if low in _NEGATIVE or low.startswith(("no, ", "still ", "it still")):
        return MessageRelation.REJECTION if _is_question(previous) else MessageRelation.CONSTRAINT_UPDATE
    if any(low.startswith(prefix) for prefix in _ACTION_STARTS):
        return MessageRelation.ACTION_REQUEST
    overlap = _overlap(text, previous_user)
    # A long, semantically unrelated request is a topic switch even if it
    # contains a demonstrative such as "these" or "that".
    if previous_user and overlap < 0.015 and len(_words(text)) >= 8:
        return MessageRelation.TOPIC_SWITCH
    if _REFERENCE_RE.search(text):
        return MessageRelation.REFERENCE
    if previous and _is_question(previous):
        return MessageRelation.ANSWER
    if overlap >= 0.12:
        return MessageRelation.CONTINUATION
    if len(_words(text)) <= 5:
        return MessageRelation.FOLLOW_UP
    return MessageRelation.EXPANSION


def resolve_reference(current: str, history: list[dict[str, str]]) -> dict[str, Any] | None:
    """Resolve references against recent discourse; return uncertainty, not a guess."""
    match = _REFERENCE_RE.search(current or "")
    if not match or not history:
        return None
    expression = match.group(0)
    candidates = [m for m in history if m["role"] in {"user", "assistant"} and m["content"].strip()]
    if not candidates:
        return None
    current_words = _words(current)
    scored = []
    for index, message in enumerate(candidates):
        score = _overlap(current, message["content"]) + (index / max(1, len(candidates))) * 0.08
        if message["role"] == "assistant" and _is_question(message["content"]):
            score += 0.03
        scored.append((score, index, message))
    score, _, selected = max(scored, key=lambda item: (item[0], item[1]))
    confidence = min(0.98, 0.55 + score)
    if len(current_words) < 2 and expression.lower() in {"it", "this", "that", "same", "again", "continue", "next"}:
        confidence = max(confidence, 0.72)
    return {
        "expression": expression,
        "resolved_text": selected["content"][-700:],
        "resolved_role": selected["role"],
        "confidence": round(confidence, 2),
    }


def rank_relevant_history(current: str, history: list[dict[str, str]], limit: int = 4) -> list[dict[str, str]]:
    """Rank prior turns by lexical relevance plus recency; always return chronological order."""
    scored: list[tuple[float, int, dict[str, str]]] = []
    total = len(history)
    for index, message in enumerate(history):
        if message["role"] == "system":
            continue
        recency = (index + 1) / max(1, total)
        lexical = _overlap(current, message["content"])
        # A reference-only follow-up benefits from the immediately preceding turns.
        score = lexical * 0.78 + recency * 0.22
        if message["role"] == "assistant" and _is_question(message["content"]):
            score += 0.04
        scored.append((score, index, message))
    chosen = sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)[:max(0, limit)]
    return [item[2] for item in sorted(chosen, key=lambda item: item[1])]


class ConversationEngine:
    """Build bounded conversation context for OM's canonical generation path."""

    def __init__(self, max_history: int | None = None, max_relevant: int | None = None, summary_chars: int | None = None):
        self.max_history = max(1, max_history or int(os.getenv("OM_CONVERSATION_MAX_HISTORY", "8")))
        self.max_relevant = max(0, max_relevant if max_relevant is not None else int(os.getenv("OM_CONVERSATION_MAX_RELEVANT", "4")))
        self.summary_chars = max(200, summary_chars or int(os.getenv("OM_CONVERSATION_SUMMARY_MAX_CHARS", "700")))

    def prepare(self, messages: list[dict[str, Any]]) -> tuple[list[dict[str, str]], ConversationState]:
        normal = _normalise(messages)
        current_index = next((i for i in range(len(normal) - 1, -1, -1) if normal[i]["role"] == "user"), -1)
        if current_index < 0:
            return normal, ConversationState(recent_messages=normal[-self.max_history:])
        current = normal[current_index]["content"]
        prior = [m for i, m in enumerate(normal[:current_index]) if m["role"] != "system"]
        state = ConversationState(
            last_user_message=current,
            last_assistant_message=next((m["content"] for m in reversed(prior) if m["role"] == "assistant"), ""),
            recent_messages=prior[-self.max_history:],
            relation=classify_relation(current, prior),
            relevant_history=rank_relevant_history(current, prior, self.max_relevant),
        )
        reference = resolve_reference(current, prior)
        if reference:
            state.references.append(reference)
        previous_user = next((m["content"] for m in reversed(prior) if m["role"] == "user"), "")
        state.previous_topic = previous_user[:180]
        state.current_topic = current[:180] if state.relation in {MessageRelation.NEW_TOPIC, MessageRelation.TOPIC_SWITCH} else (previous_user[:180] or current[:180])
        state.active_task = state.current_topic
        state.active_goal = current
        state.confidence = reference["confidence"] if reference else (0.85 if state.relation in {MessageRelation.ANSWER, MessageRelation.CONTINUATION, MessageRelation.REFERENCE} else 0.65)
        state.task_status = "active" if prior else "new"
        assistant_turns = [m["content"] for m in prior if m["role"] == "assistant"]
        state.pending_question = assistant_turns[-1][-240:] if assistant_turns and _is_question(assistant_turns[-1]) else ""
        state.unresolved_questions = [state.pending_question] if state.pending_question else []
        if state.relevant_history:
            state.summary = " | ".join(f'{m["role"]}: {m["content"][:180]}' for m in state.relevant_history)[-self.summary_chars:]
        if not prior:
            return normal, state

        # Keep system instructions, recent turns, and relevant older turns. Never drop the current user turn.
        recent_start = max(0, current_index - self.max_history)
        selected_indices = {i for i, m in enumerate(normal) if m["role"] == "system"}
        selected_indices.update(range(recent_start, current_index))
        for item in state.relevant_history:
            for i in range(current_index):
                if normal[i]["role"] == item["role"] and normal[i]["content"] == item["content"]:
                    selected_indices.add(i)
                    break
        selected_indices.add(current_index)
        bounded = [normal[i] for i in sorted(selected_indices)]
        context_lines = [
            "Use this conversation state to interpret follow-ups; the latest user message remains the primary instruction.",
            f"Relation: {state.relation.value}.",
            f"Active task/topic: {state.active_task[:180]}",
        ]
        if state.pending_question:
            context_lines.append(f"Pending question from the assistant: {state.pending_question}")
        if reference:
            context_lines.append(
                f'Reference "{reference["expression"]}" most likely points to the {reference["resolved_role"]} turn: {reference["resolved_text"][:260]} (confidence {reference["confidence"]}). If ambiguous, ask a concise clarification.'
            )
        if state.summary:
            context_lines.append(f"Relevant history: {state.summary}")
        context = "\n".join(context_lines)[:self.summary_chars + 700]
        # Insert as a system message after any existing system messages.
        first_non_system = next((i for i, m in enumerate(bounded) if m["role"] != "system"), len(bounded))
        bounded.insert(first_non_system, {"role": "system", "content": "Conversation context (derived from prior turns):\n" + context})
        return bounded, state
