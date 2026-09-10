"""STEP 89 — Long Context Intelligence.

Conversation memory → summarization → importance ranking → recall.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class ConversationMemory:
    def __init__(self, path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self.path = Path(path or root / "data" / "om-memory" / "long_context.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.turns: list[dict[str, Any]] = []

    def add(self, role: str, content: str) -> None:
        turn = {"ts": time.time(), "role": role, "content": (content or "")[:4000]}
        self.turns.append(turn)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")

    def recent(self, n: int = 12) -> list[dict[str, Any]]:
        return self.turns[-n:]


class ContextSummarizer:
    def summarize(self, turns: list[dict[str, Any]], *, max_chars: int = 1200) -> str:
        if not turns:
            return ""
        parts = []
        for t in turns:
            role = t.get("role", "user")
            content = str(t.get("content") or "").strip().replace("\n", " ")
            if content:
                parts.append(f"{role}: {content[:220]}")
        text = " | ".join(parts)
        if len(text) <= max_chars:
            return text
        head = text[: max_chars // 2]
        tail = text[-max_chars // 2 :]
        return head + " … " + tail


class ImportanceRanker:
    def rank(self, items: list[str], query: str, *, top_k: int = 8) -> list[str]:
        q = set((query or "").lower().split())
        scored = []
        for item in items:
            if not item:
                continue
            words = set(str(item).lower().split())
            score = len(q & words)
            # Prefer facts / decisions
            low = str(item).lower()
            if any(k in low for k in ("decided", "prefer", "must", "version", "api", "user")):
                score += 2
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in scored[:top_k]]


class RecallEngine:
    def recall(
        self,
        query: str,
        *,
        memory_items: list[Any] | None = None,
        turns: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        memory_items = memory_items or []
        turns = turns or []
        summarizer = ContextSummarizer()
        ranker = ImportanceRanker()
        summary = summarizer.summarize(turns)
        flat = [str(m) for m in memory_items if m] + [
            f"{t.get('role')}: {t.get('content')}" for t in turns
        ]
        important = ranker.rank(flat, query)
        packed = "\n".join(
            [
                "Conversation summary:",
                summary or "(none)",
                "",
                "Important facts:",
                *[f"- {x}" for x in important[:8]],
            ]
        )
        return {
            "step": 89,
            "summary": summary,
            "important": important,
            "context": packed[:6000],
        }


class LongContextIntelligence:
    def __init__(self) -> None:
        self.memory = ConversationMemory()
        self.summarizer = ContextSummarizer()
        self.ranker = ImportanceRanker()
        self.recall_engine = RecallEngine()

    def process(
        self,
        query: str,
        *,
        memory_items: list[Any] | None = None,
        prior_turns: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if prior_turns:
            for t in prior_turns[-8:]:
                self.memory.add(str(t.get("role") or "user"), str(t.get("content") or ""))
        self.memory.add("user", query)
        recalled = self.recall_engine.recall(
            query,
            memory_items=memory_items,
            turns=self.memory.recent(20),
        )
        return recalled
