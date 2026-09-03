"""Autonomous search decision — use research when knowledge is missing."""
from __future__ import annotations

from typing import Any


class AutonomousResearch:
    """Decide whether external knowledge is needed, then collect/summarize/store."""

    def __init__(self) -> None:
        try:
            from om_ai.research.agent import ResearchAgent

            self.agent = ResearchAgent()
        except Exception:
            self.agent = None

    def maybe_research(
        self,
        question: str,
        *,
        understanding: dict[str, Any] | None = None,
        knowledge_packets: list | None = None,
    ) -> dict[str, Any]:
        u = understanding or {}
        packets = knowledge_packets or []
        has_local = any(
            (isinstance(p, dict) and (p.get("texts") or p.get("text")))
            for p in packets
        )
        intent = str(u.get("intent") or "")
        domain = str(u.get("domain") or "")
        needs = (
            intent in {"research", "explanation", "question"}
            or domain in {"science", "ai", "research"}
        ) and not has_local

        # Freshness cues without hard topic locks
        q = (question or "").lower()
        if any(x in q for x in ("latest", "today news", "recent paper", "2024", "2025", "2026")):
            needs = True

        if not needs:
            return {"needed": False, "used": False, "summary": "", "sources": []}

        summary = ""
        sources: list[str] = []
        if self.agent is not None:
            try:
                if hasattr(self.agent, "research"):
                    result = self.agent.research(question)
                elif hasattr(self.agent, "execute"):
                    result = self.agent.execute(question, {})
                else:
                    result = {"summary": f"Research planned for: {question}"}
                if isinstance(result, dict):
                    summary = str(result.get("summary") or result.get("answer") or result)[:2000]
                    sources = list(result.get("sources") or result.get("retrieval") or [])[:10]
                else:
                    summary = str(result)[:2000]
            except Exception as exc:
                summary = f"Research attempted but unavailable ({exc})."
        else:
            summary = (
                f"External knowledge likely needed for “{question}”. "
                "Research agent is not fully configured; using reasoning fallback."
            )

        # Store into experience memory softly
        try:
            from pathlib import Path
            import json
            from datetime import datetime, timezone

            path = Path("data/om-memory/research_cache.json")
            path.parent.mkdir(parents=True, exist_ok=True)
            rows = []
            if path.exists():
                rows = json.loads(path.read_text() or "[]")
            if not isinstance(rows, list):
                rows = []
            rows.append(
                {
                    "question": question,
                    "summary": summary[:1000],
                    "time": datetime.now(timezone.utc).isoformat(),
                }
            )
            path.write_text(json.dumps(rows[-100:], indent=2))
        except Exception:
            pass

        return {"needed": True, "used": True, "summary": summary, "sources": sources}
