"""Rank conversation history and durable memory for grounded follow-up answers.

This module deliberately uses a small deterministic lexical ranker so it remains
available in offline/native-only deployments. It is context selection, not a
replacement for the language model.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "could", "did", "do", "does", "for", "from", "had", "has", "have", "how",
    "i", "if", "in", "into", "is", "it", "its", "me", "my", "of", "on", "or",
    "our", "please", "should", "so", "that", "the", "their", "them", "there",
    "these", "they", "this", "those", "to", "us", "was", "we", "were", "what",
    "when", "where", "which", "who", "why", "will", "with", "would", "you",
    "your",
}
_REFERENCE_WORDS = {
    "again", "above", "earlier", "it", "same", "that", "these", "this",
    "those", "previous", "problem", "issue", "code", "file",
}


class ContextRetriever:
    """Select a compact, relevant blend of recent turns and durable memory."""

    def retrieve(
        self,
        message: str,
        history: Iterable[dict[str, Any]] | None = None,
        memory: Any = None,
        limit: int = 6,
    ) -> dict[str, list[dict[str, Any]]]:
        turns = [
            {"role": str(item.get("role") or "user"), "content": str(item.get("content") or "")}
            for item in (history or [])
            if isinstance(item, dict) and str(item.get("content") or "").strip()
        ]
        limit = max(0, min(int(limit), 20))
        if not limit:
            return {"history": [], "memory": []}

        query_tokens = self._tokens(message)
        is_reference = bool(query_tokens & _REFERENCE_WORDS)
        ranked: list[tuple[float, int, dict[str, Any]]] = []
        total = max(len(turns), 1)

        for index, turn in enumerate(turns):
            text_tokens = self._tokens(turn["content"])
            overlap = len(query_tokens & text_tokens)
            # Recency is a tie-breaker, not a substitute for semantic overlap.
            recency = (index + 1) / total
            role_weight = 1.08 if turn["role"] == "user" else 1.0
            reference_bonus = 0.35 if is_reference else 0.0
            score = role_weight * (overlap * 2.0) + recency * 0.45 + reference_bonus
            if not query_tokens or overlap:
                ranked.append((score, index, turn))

        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected = [item[2] for item in ranked[:limit]]

        # Preserve chronology in the final prompt after ranking has chosen the hits.
        selected_ids = {index for _, index, _ in ranked[:limit]}
        selected = [turn for index, turn in enumerate(turns) if index in selected_ids]

        memory_hits: list[dict[str, Any]] = []
        if memory is not None:
            try:
                recalled = memory.recall(message, k=limit) or []
                for item in recalled[:limit]:
                    if isinstance(item, dict):
                        memory_hits.append(item)
                    elif isinstance(item, str) and item.strip():
                        memory_hits.append({"content": item.strip()})
            except Exception:
                # Memory is an optional enhancement; a retrieval outage must not
                # prevent the current user turn from being answered.
                memory_hits = []

        return {"history": selected, "memory": memory_hits}

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-zA-Z0-9_+#.-]{2,}", (text or "").lower())
            if token not in _STOP_WORDS
        }
