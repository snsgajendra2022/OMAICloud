"""STEP 94.10 — Teacher Intelligence.

Track which teachers win on which domains, recommend routing, and score reliability.
Uses harvest ranking outcomes only (API outputs) — never private weights.
"""
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


def _repo_data() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "om_distillation" / "teacher_intel"


_DOMAIN_CUES: dict[str, tuple[str, ...]] = {
    "software": ("react", "api", "code", "typescript", "laravel", "python", "component"),
    "devops": ("kubernetes", "docker", "ci", "deploy", "pipeline", "infra"),
    "security": ("auth", "permission", "encrypt", "tenant", "audit", "oauth"),
    "data": ("database", "sql", "queue", "cache", "schema", "storage"),
    "architecture": ("architecture", "design", "system", "scale", "microservice"),
}


class TeacherIntelligence:
    """STEP 94.10 — learn teacher strengths from ranked distillations."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else _repo_data()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "profiles.json"
        self._state = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"teachers": {}, "updated_at": None}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"teachers": {}, "updated_at": None}

    def _save(self) -> None:
        self._state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    def detect_domain(self, text: str) -> str:
        low = (text or "").lower()
        scores = {
            dom: sum(1 for c in cues if c in low) for dom, cues in _DOMAIN_CUES.items()
        }
        best = max(scores, key=scores.get) if scores else "general"
        return best if scores.get(best, 0) > 0 else "general"

    def record(
        self,
        task: str,
        ranking: dict[str, Any] | None,
        *,
        latency_by_teacher: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Update profiles from a ranked harvest."""
        ranking = ranking or {}
        domain = self.detect_domain(task)
        teachers = self._state.setdefault("teachers", {})
        for row in ranking.get("ranked") or []:
            pid = str(row.get("provider") or row.get("teacher") or "unknown")
            prof = teachers.setdefault(
                pid,
                {
                    "wins": 0,
                    "passes": 0,
                    "fails": 0,
                    "total": 0,
                    "score_sum": 0.0,
                    "domains": {},
                    "avg_latency_ms": 0.0,
                    "latency_n": 0,
                },
            )
            score = float(row.get("score") or 0.0)
            prof["total"] += 1
            prof["score_sum"] += score
            if row.get("pass"):
                prof["passes"] += 1
            else:
                prof["fails"] += 1
            dom = prof["domains"].setdefault(domain, {"n": 0, "score_sum": 0.0, "wins": 0})
            dom["n"] += 1
            dom["score_sum"] += score
            if latency_by_teacher and pid in latency_by_teacher:
                n = int(prof["latency_n"]) + 1
                prev = float(prof["avg_latency_ms"])
                lat = float(latency_by_teacher[pid])
                prof["avg_latency_ms"] = ((prev * (n - 1)) + lat) / n
                prof["latency_n"] = n

        best = ranking.get("best") or {}
        winner = str(best.get("provider") or best.get("teacher") or "")
        if winner and winner in teachers:
            teachers[winner]["wins"] += 1
            d = teachers[winner]["domains"].setdefault(domain, {"n": 0, "score_sum": 0.0, "wins": 0})
            d["wins"] = int(d.get("wins") or 0) + 1

        self._save()
        return {"domain": domain, "winner": winner or None, "teachers": list(teachers)}

    def profile(self, teacher: str) -> dict[str, Any]:
        raw = (self._state.get("teachers") or {}).get(teacher) or {}
        total = max(1, int(raw.get("total") or 0))
        domains = {}
        for dom, stats in (raw.get("domains") or {}).items():
            n = max(1, int(stats.get("n") or 0))
            domains[dom] = {
                "avg_score": round(float(stats.get("score_sum") or 0) / n, 3),
                "wins": int(stats.get("wins") or 0),
                "n": int(stats.get("n") or 0),
            }
        return {
            "teacher": teacher,
            "total": int(raw.get("total") or 0),
            "wins": int(raw.get("wins") or 0),
            "pass_rate": round(int(raw.get("passes") or 0) / total, 3),
            "avg_score": round(float(raw.get("score_sum") or 0) / total, 3),
            "avg_latency_ms": round(float(raw.get("avg_latency_ms") or 0), 1),
            "domains": domains,
            "specialty": max(domains, key=lambda d: domains[d]["avg_score"]) if domains else None,
        }

    def recommend_teachers(self, task: str, *, limit: int = 3) -> list[dict[str, Any]]:
        domain = self.detect_domain(task)
        scored: list[dict[str, Any]] = []
        for name in (self._state.get("teachers") or {}):
            p = self.profile(name)
            dom = (p.get("domains") or {}).get(domain) or {}
            strength = float(dom.get("avg_score") or p.get("avg_score") or 0)
            scored.append(
                {
                    "teacher": name,
                    "domain": domain,
                    "strength": strength,
                    "specialty": p.get("specialty"),
                    "pass_rate": p.get("pass_rate"),
                }
            )
        scored.sort(key=lambda x: (x["strength"], x["pass_rate"]), reverse=True)
        if scored:
            return scored[:limit]
        # Cold start — default catalog order
        return [
            {"teacher": t, "domain": domain, "strength": 0.5, "specialty": None, "pass_rate": 0.0}
            for t in ("gpt", "claude", "gemini", "qwen")[:limit]
        ]

    def status(self) -> dict[str, Any]:
        teachers = {
            name: self.profile(name) for name in (self._state.get("teachers") or {})
        }
        return {
            "step": "94.10",
            "name": "Teacher Intelligence",
            "teachers": teachers,
            "updated_at": self._state.get("updated_at"),
            "path": str(self.path),
        }
