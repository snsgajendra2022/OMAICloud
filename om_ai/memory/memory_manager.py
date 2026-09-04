"""
OM Advanced Memory Manager (STEP 80.13)

Short Term + Long Term + Personal/Semantic + Episodic/Experience + Learning

Structure:
  short_term.py
  long_term.py
  episodic_memory.py
  semantic_memory.py
  memory_manager.py  ← this facade (AdvancedMemorySystem)
"""
from __future__ import annotations

import os
from typing import Any

from om_ai.memory.short_term import ShortTermMemory
from om_ai.memory.long_term import LongTermMemory
from om_ai.memory.episodic_memory import EpisodicMemory
from om_ai.memory.semantic_memory import SemanticMemory
from om_ai.memory.storage import MemoryStorage
from om_ai.memory.conversation import ConversationMemory


def advanced_memory_enabled() -> bool:
    return os.environ.get("OM_ADVANCED_MEMORY", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


class AdvancedMemorySystem:
    """Unified memory brain for chat + agents + knowledge graph growth."""

    def __init__(
        self,
        *,
        tenant_id: str = "default",
        user_id: str = "default",
        project_id: str | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.user_id = user_id or "default"
        self.project_id = project_id
        self.storage = MemoryStorage()
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(
            path=os.environ.get(
                "OM_LONG_TERM_MEMORY",
                "data/om-memory/long_term_memory.json",
            )
        )
        self.episodic = EpisodicMemory(self.storage)
        self.semantic = SemanticMemory(self.storage)
        self.conversation = ConversationMemory()
        # Also bridge to SQLite layered store when available
        try:
            from om_ai.memory.layers import LayeredMemory

            self.layered = LayeredMemory(
                tenant_id=tenant_id,
                user_id=self.user_id,
            )
        except Exception:
            self.layered = None

    # ── write paths ──────────────────────────────────────────────────
    def remember_turn(self, user: str, assistant: str) -> None:
        self.conversation.add_user_message(user)
        self.conversation.add_assistant_message(assistant)
        self.short_term.remember("last_user", user)
        self.short_term.remember("last_assistant", (assistant or "")[:2000])
        # Extract simple personal facts
        self._maybe_extract_personal(user)
        if self.layered is not None:
            try:
                self.layered.remember("conversation", f"User: {user}\nOM: {assistant[:500]}")
            except Exception:
                pass

    def remember_experience(self, question: str, solution: str, score: float = 0.75) -> int:
        eid = self.episodic.remember(question, solution, score=score)
        self.long_term.remember(
            "decisions",
            {"question": question[:200], "score": score},
        )
        if self.layered is not None:
            try:
                self.layered.remember(
                    "experience",
                    f"Q: {question}\nA: {solution[:800]}",
                    metadata={"score": score},
                )
            except Exception:
                pass
        # Grow knowledge graph lightly
        self._grow_graph(question, solution)
        return eid

    def remember_fact(self, content: str, *, importance: float = 0.8) -> int:
        sid = self.semantic.remember(content, kind="fact", importance=importance)
        self.long_term.remember("facts", content)
        if self.layered is not None:
            try:
                self.layered.remember("user", content, metadata={"kind": "fact"})
            except Exception:
                pass
        # Keep core.memory twin in sync (connected, not deleted)
        try:
            from om_ai.core.memory.memory_manager import MemoryManager as CoreMemoryManager

            CoreMemoryManager().remember(content)
        except Exception:
            pass
        return sid

    def remember_preference(self, content: str) -> int:
        pid = self.semantic.remember_preference(content)
        self.long_term.remember("preferences", content)
        return pid

    def _maybe_extract_personal(self, text: str) -> None:
        t = (text or "").strip()
        low = t.lower()
        if low.startswith("my name is ") or low.startswith("i am ") or "मेरा नाम" in t:
            self.remember_preference(t[:160])
        if "i prefer" in low or "मुझे पसंद" in t:
            self.remember_preference(t[:160])

    def _grow_graph(self, question: str, solution: str) -> None:
        try:
            from om_ai.knowledge.graph.engine import KnowledgeGraphEngine

            blob = f"{question}\n{solution}"
            # Simple entity dict from capitalized / tech tokens
            data: dict[str, str] = {}
            for tok in (question + " " + solution).split():
                clean = tok.strip(".,;:()[]{}\"'").strip()
                if len(clean) >= 3 and clean[0].isupper():
                    data[clean.lower()] = clean
                if clean.lower() in {
                    "python",
                    "react",
                    "laravel",
                    "php",
                    "composer",
                    "fastapi",
                    "india",
                    "ai",
                }:
                    data[clean.lower()] = clean
            if data:
                KnowledgeGraphEngine().process(data, "memory")
        except Exception:
            pass

    # ── read paths ───────────────────────────────────────────────────
    def recall(
        self,
        query: str,
        *,
        k: int = 8,
        include_short: bool = True,
    ) -> dict[str, Any]:
        """Recall across all layers for reasoning / chat grounding."""
        episodic = self.episodic.recall(query, k=k)
        semantic = self.semantic.recall(query, k=k)
        layered_hits: list[dict[str, Any]] = []
        if self.layered is not None:
            try:
                layered_hits = self.layered.recall(query, k=k)
            except Exception:
                layered_hits = []

        snippets: list[str] = []
        for h in semantic[:3]:
            snippets.append(f"[personal] {h['content'][:240]}")
        for h in episodic[:3]:
            snippets.append(f"[experience] {h['content'][:240]}")
        for h in layered_hits[:3]:
            snippets.append(f"[layered] {str(h.get('content') or '')[:240]}")

        short = self.short_term.all() if include_short else {}
        conv = ""
        try:
            conv = self.conversation.get_context()
        except Exception:
            conv = ""

        return {
            "short_term": short,
            "conversation": conv,
            "episodic": episodic,
            "semantic": semantic,
            "layered": layered_hits,
            "snippets": snippets,
            "long_term_facts": self.long_term.recall("facts")[-5:],
            "long_term_preferences": self.long_term.recall("preferences")[-5:],
        }

    def context_for_prompt(self, query: str, *, limit: int = 6) -> str:
        pack = self.recall(query, k=limit)
        lines = list(pack.get("snippets") or [])[:limit]
        prefs = pack.get("long_term_preferences") or []
        for p in prefs[-2:]:
            lines.append(f"[preference] {p}")
        return "\n".join(lines)

    def learn_from_feedback(
        self,
        question: str,
        answer: str,
        *,
        score: float,
        feedback: str = "",
    ) -> dict[str, Any]:
        """Controlled learning memory — only store when score/feedback warrants it."""
        if score >= 0.7:
            eid = self.remember_experience(question, answer, score=score)
            return {"stored": True, "type": "experience", "id": eid}
        if feedback and len(feedback) > 8:
            fid = self.remember_fact(f"Feedback: {feedback} | Q: {question[:120]}", importance=0.6)
            return {"stored": True, "type": "feedback", "id": fid}
        return {"stored": False, "reason": "score_too_low"}


# Back-compat for brain_pipeline / older scripts (prefer AdvancedMemorySystem)
class MemoryManager(AdvancedMemorySystem):
    """Unified manager + legacy API (get_context list, get_relevant_memory)."""

    def remember_conversation(self, question: str, answer: str = "") -> None:
        self.remember_turn(question or "", answer or "")
        try:
            from om_ai.memory.extractor import MemoryExtractor

            for item in MemoryExtractor().extract(str(question or "")) or []:
                if item:
                    self.remember_fact(str(item), importance=0.75)
        except Exception:
            pass

    def get_context(self) -> list[Any]:
        """Legacy: list of memory content strings (newest first)."""
        rows = self.storage.all() or []
        return [row[1] for row in rows[:20] if len(row) > 1 and row[1]]

    def get_relevant_memory(
        self,
        question: str,
        memories: list | None = None,
    ) -> Any:
        if memories is None:
            memories = self.get_context()
        try:
            from om_ai.memory.semantic_search import SemanticMemorySearch

            return SemanticMemorySearch().search(question, memories)
        except Exception:
            pack = self.recall(question or "", k=5)
            return list(pack.get("snippets") or [])

    def remember_project(self, project: str, description: str) -> int:
        from om_ai.memory.models import MemoryItem

        return int(
            self.storage.save(
                MemoryItem(
                    id=None,
                    content=description,
                    memory_type="project",
                    project=project,
                    importance=0.9,
                )
            )
        )

    def remember_experience(  # type: ignore[override]
        self,
        question: str,
        solution: str,
        score: float = 0.75,
    ) -> int:
        return super().remember_experience(question, solution, score=float(score))

    def context_pack(self, query: str = "") -> dict[str, Any]:
        """Full advanced recall dict (new API)."""
        return self.recall(query or str(self.short_term.recall("last_user") or ""))