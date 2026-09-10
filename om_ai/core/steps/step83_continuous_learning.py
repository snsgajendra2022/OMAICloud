"""STEP 83 — Continuous Learning Intelligence.

Flow: answer → was it good? → what failed? → store experience → improve next time.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class ContinuousLearningIntelligence:
    """Online learning loop after every OM answer."""

    def __init__(self, store_path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self.store_path = Path(
            store_path
            or root / "data" / "om-memory" / "continuous_learning.jsonl"
        )
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.skills: dict[str, float] = {}
        self._load_skills()

    def _skills_path(self) -> Path:
        return self.store_path.with_name("skill_growth.json")

    def _load_skills(self) -> None:
        p = self._skills_path()
        if p.exists():
            try:
                self.skills = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                self.skills = {}

    def _save_skills(self) -> None:
        self._skills_path().write_text(
            json.dumps(self.skills, indent=2), encoding="utf-8"
        )

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        quality = quality or {}
        score = float(quality.get("score") or 0.0)
        approved = bool(quality.get("approved", False))
        issues = list(quality.get("issues") or [])

        text = (answer or "").strip()
        if not text:
            score = 0.0
            approved = False
            issues.append("empty")
        elif len(text.split()) < 4:
            score = min(score, 0.3)
            issues.append("too_short")
        elif approved and score < 0.5:
            score = 0.7

        domain = self._domain(question)
        return {
            "approved": approved and score >= 0.55 and not issues,
            "score": score if score else (0.8 if approved else 0.35),
            "issues": issues,
            "domain": domain,
            "success": approved and score >= 0.55,
        }

    def _domain(self, question: str) -> str:
        q = (question or "").lower()
        if any(w in q for w in ("code", "react", "api", "python", "build", "app")):
            return "coding"
        if any(w in q for w in ("latest", "news", "version", "price")):
            return "research"
        if any(w in q for w in ("architect", "design", "scale", "system")):
            return "architecture"
        return "general"

    def learn(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        evaluation = self.evaluate_answer(question, answer, quality)
        domain = evaluation["domain"]
        prev = float(self.skills.get(domain, 0.5))
        delta = 0.05 if evaluation["success"] else -0.03
        self.skills[domain] = max(0.05, min(0.99, prev + delta))
        self._save_skills()

        record = {
            "ts": time.time(),
            "question": (question or "")[:500],
            "answer": (answer or "")[:1000],
            "evaluation": evaluation,
            "skill": self.skills[domain],
            "meta": meta or {},
        }
        with self.store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        suggestions = []
        if not evaluation["success"]:
            suggestions.append("Tighten answer structure and verify facts next time.")
            for issue in evaluation["issues"][:5]:
                suggestions.append(f"Fix issue: {issue}")
        else:
            suggestions.append("Reinforce successful pattern for this domain.")

        return {
            "step": 83,
            "status": "learned",
            "evaluation": evaluation,
            "skill_growth": {domain: self.skills[domain]},
            "suggestions": suggestions,
            "store": str(self.store_path),
        }

    def skill_snapshot(self) -> dict[str, float]:
        return dict(self.skills)
