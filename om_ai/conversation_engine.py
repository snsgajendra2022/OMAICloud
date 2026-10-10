"""Canonical conversation-context resolver for OM AI.

This module is deliberately deterministic: it selects relevant prior turns and
optional durable-memory hits, then supplies compact context to later reasoning
stages. It does not generate an answer or claim semantic understanding it cannot
verify.
"""
from __future__ import annotations

import re
from typing import Any

_WORDS = re.compile(r"[a-zA-Z0-9_'-]+")
_REFERENCE_WORDS = {
    "it", "this", "that", "these", "those", "they", "them", "there",
    "same", "also", "continue", "previous", "above", "before", "again",
    "he", "she", "we", "you", "your", "its", "their",
}


def _tokens(text: str) -> set[str]:
    return {word.lower() for word in _WORDS.findall(text) if len(word) > 1}


def _overlap_score(query_tokens: set[str], text: str) -> float:
    tokens = _tokens(text)
    if not query_tokens or not tokens:
        return 0.0
    return len(query_tokens & tokens) / max(1, len(query_tokens))


def _topic(text: str) -> str:
    words = [w.lower() for w in _WORDS.findall(text) if len(w) > 2]
    stop = {
        "the", "and", "for", "you", "your", "that", "this", "with", "from",
        "what", "when", "where", "why", "how", "can", "could", "would",
        "please", "help", "about", "have", "has", "are", "was", "were",
    }
    useful = [w for w in words if w not in stop]
    return " ".join(useful[:6]) or "general conversation"


class ConversationEngine:
    """Resolve follow-up relation, relevant history, and durable memory."""

    def process(
        self,
        user_text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        tenant_id: str = "default",
        actor: str = "",
        conversation_id: str | None = None,
        durable_memory: Any = None,
        max_history_turns: int = 8,
    ) -> dict[str, Any]:
        query = (user_text or "").strip()
        turns: list[dict[str, str]] = []
        for item in history or []:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").lower().strip()
            content = str(item.get("content") or "").strip()
            if role in {"user", "assistant", "system"} and content:
                turns.append({"role": role, "content": content[:2000]})
        turns = turns[-max(1, int(max_history_turns)):]

        q_tokens = _tokens(query)
        lowered = query.lower()
        is_followup = bool(
            re.search(r"\b(it|this|that|these|those|they|them|same|also|continue|previous|above|again)\b", lowered)
            or len(q_tokens) <= 5
        )
        relevant: list[dict[str, str]] = []
        for index, turn in enumerate(turns):
            score = _overlap_score(q_tokens, turn["content"])
            # Recent turns are useful for pronoun/reference follow-ups even
            # when lexical overlap is low.
            recency_bonus = (index + 1) / max(1, len(turns))
            if score >= 0.12 or (is_followup and recency_bonus >= 0.5):
                relevant.append({**turn, "relevance": round(score, 3)})  # type: ignore[dict-item]
        relevant = relevant[-6:]

        memory_hits: list[dict[str, Any]] = []
        if durable_memory is not None and query:
            try:
                raw_hits = durable_memory.recall(query, k=4) or []
                for hit in raw_hits[:4]:
                    if isinstance(hit, dict) and str(hit.get("content") or "").strip():
                        memory_hits.append({
                            "content": str(hit.get("content"))[:1200],
                            "kind": str(hit.get("kind") or ""),
                            "id": str(hit.get("id") or ""),
                        })
            except Exception:
                # Memory must never make chat fail; absence is not evidence of a hit.
                memory_hits = []

        relation = "follow_up" if is_followup and turns else ("new_topic" if turns else "new_conversation")
        active_task = ""
        for turn in reversed(turns):
            if turn["role"] == "user":
                active_task = turn["content"][:240]
                break

        references = sorted(q_tokens & _REFERENCE_WORDS)
        analysis = {
            "topic": _topic(query),
            "active_task": active_task,
            "references": references,
            "relevant_history": relevant,
            "memory_hits": memory_hits,
        }
        context_lines: list[str] = []
        if relevant:
            context_lines.append("Relevant conversation history:")
            context_lines.extend(
                f"- {turn['role']}: {turn['content']}" for turn in relevant
            )
        if memory_hits:
            context_lines.append("Relevant saved memory:")
            context_lines.extend(f"- {hit['content']}" for hit in memory_hits)
        context_blob = "\n".join(context_lines)
        return {
            "relation": relation,
            "analysis": analysis,
            "context_blob": context_blob,
            "tenant_id": tenant_id or "default",
            "actor": actor or "default",
            "conversation_id": conversation_id,
        }
