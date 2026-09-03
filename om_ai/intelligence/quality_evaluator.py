"""Quality gate — regenerate if score < threshold."""
from __future__ import annotations

import re
from typing import Any


class QualityEvaluator:
    def evaluate(
        self,
        question: str,
        answer: str,
        *,
        intent: dict[str, Any] | None = None,
        understanding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        q = (question or "").strip()
        a = (answer or "").strip()
        intent = intent or {}
        understanding = understanding or {}
        issues: list[str] = []
        score = 100.0

        if not a:
            return {"score": 0.0, "passed": False, "issues": ["empty answer"], "needs_regenerate": True}

        # Intent coverage: answer should relate to question tokens
        q_tokens = set(re.findall(r"[a-z0-9]+", q.lower())) - {
            "a", "an", "the", "for", "to", "of", "and", "or", "is", "me", "my", "please",
        }
        a_low = a.lower()
        if q_tokens:
            hit = sum(1 for t in q_tokens if t in a_low)
            cover = hit / max(1, len(q_tokens))
            if cover < 0.15 and intent.get("intent") not in {"chat", "datetime"}:
                score -= 25
                issues.append("weak intent coverage")

        # Hallucination / pipeline chrome
        if re.search(r"(?i)\b(agents?:|intent:|self-critique|pipeline)\b", a):
            score -= 30
            issues.append("internal chrome leaked")

        if len(a) < 12:
            score -= 20
            issues.append("too short")

        # Completeness heuristics by style cues
        action = str(understanding.get("required_action") or "")
        if action in {"generate", "create"} and len(a) < 80:
            score -= 15
            issues.append("generation likely incomplete")

        if intent.get("intent") == "datetime" and not re.search(r"\d{4}|\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", a, re.I):
            score -= 40
            issues.append("missing date content")

        score = max(0.0, min(100.0, score))
        passed = score >= 80.0
        return {
            "score": score,
            "passed": passed,
            "issues": issues,
            "needs_regenerate": not passed,
        }

    def regenerate(
        self,
        question: str,
        previous: str,
        evaluation: dict[str, Any],
        planner: Any,
        **kwargs: Any,
    ) -> str:
        """Second-pass draft with stricter balanced style."""
        understanding = kwargs.get("understanding") or {}
        intent = kwargs.get("intent") or {}
        style = {"style": "balanced", "tone": "helpful_direct", "ask_followup": True}
        draft = planner.draft(
            question,
            understanding,
            intent,
            style,
            knowledge=kwargs.get("knowledge"),
            memory=kwargs.get("memory"),
            agents=kwargs.get("agents"),
            context=kwargs.get("context"),
        )
        note = ""
        if evaluation.get("issues"):
            note = ""
        return (draft or previous or "").strip() + ("\n" if draft else "")
