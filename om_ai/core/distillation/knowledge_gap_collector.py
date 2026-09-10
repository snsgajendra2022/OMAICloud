"""STEP 94.13 — Knowledge Gap Collector.

Find weak/missing topics from chat quality, failed distillations, and explicit marks.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any


def _repo_data() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "om_distillation" / "gaps"


_WEAK = re.compile(
    r"("
    r"i don't know|i do not know|not sure|cannot answer|"
    r"om could not generate|no reliable response|"
    r"as an ai|lorem ipsum|\[tool:"
    r")",
    re.I,
)


class KnowledgeGapCollector:
    """STEP 94.13 — collect and prioritize knowledge gaps for curriculum/harvest."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else _repo_data()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "gaps.jsonl"

    def _append(self, row: dict[str, Any]) -> dict[str, Any]:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def _topic_from_question(self, question: str) -> str:
        q = re.sub(r"\s+", " ", (question or "").strip())
        # Strip common question prefixes
        q = re.sub(
            r"^(what is|what's|how (do|to|does|can)|explain|build|design|create)\s+",
            "",
            q,
            flags=re.I,
        )
        return (q[:80] or "unknown").strip(" ?.!")

    def collect_from_turn(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        quality = quality or {}
        score = float(quality.get("score") or 0.0)
        ans = (answer or "").strip()
        q = (question or "").strip()
        if not q:
            return None
        weak = bool(_WEAK.search(ans)) or score < 0.45 or len(ans) < 40
        if not weak and score >= 0.7:
            return None
        row = {
            "id": f"gap_{uuid.uuid4().hex[:10]}",
            "topic": self._topic_from_question(q),
            "question": q,
            "reason": "low_quality" if score < 0.45 else ("weak_answer" if weak else "borderline"),
            "score": score,
            "source": "chat_turn",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return self._append(row)

    def collect_from_ranking(
        self,
        question: str,
        ranking: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        ranking = ranking or {}
        best = ranking.get("best")
        pass_count = int(ranking.get("pass_count") or 0)
        if best and pass_count > 0 and float(best.get("score") or 0) >= 0.55:
            return None
        row = {
            "id": f"gap_{uuid.uuid4().hex[:10]}",
            "topic": self._topic_from_question(question),
            "question": question,
            "reason": "teachers_failed_quality_gate",
            "score": float((best or {}).get("score") or 0.0),
            "source": "distillation",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return self._append(row)

    def collect_explicit(self, topic: str, *, question: str | None = None) -> dict[str, Any]:
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        row = {
            "id": f"gap_{uuid.uuid4().hex[:10]}",
            "topic": topic,
            "question": (question or f"Explain {topic} in depth with practical guidance.").strip(),
            "reason": "explicit",
            "score": 0.0,
            "source": "manual",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return self._append(row)

    def list_gaps(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        return rows[-limit:]

    def top_gaps(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Dedupe by topic, prefer lower scores / explicit reasons."""
        buckets: dict[str, dict[str, Any]] = {}
        for row in self.list_gaps(limit=500):
            topic = str(row.get("topic") or "").lower()
            if not topic:
                continue
            prev = buckets.get(topic)
            if prev is None or float(row.get("score") or 0) <= float(prev.get("score") or 1):
                buckets[topic] = row
        ranked = sorted(
            buckets.values(),
            key=lambda r: (
                0 if r.get("reason") == "explicit" else 1,
                float(r.get("score") or 0.0),
            ),
        )
        return ranked[:limit]

    def export_questions(self, *, limit: int = 20) -> list[str]:
        return [str(g.get("question") or "") for g in self.top_gaps(limit=limit) if g.get("question")]

    def status(self) -> dict[str, Any]:
        gaps = self.list_gaps(limit=1000)
        return {
            "step": "94.13",
            "name": "Knowledge Gap Collector",
            "total": len(gaps),
            "top": self.top_gaps(limit=5),
            "path": str(self.path),
        }
