"""Rank teacher answers by structure, coverage, and safety signals."""
from __future__ import annotations

import re
from typing import Any


_BAD = re.compile(
    r"("
    r"i cannot help with illegal|"
    r"as an ai language model i cannot provide|"
    r"\[tool:|"
    r"genesis knowledge map|"
    r"lorem ipsum|"
    r"asdfgh|"
    r"http://example\.com/secret"
    r")",
    re.I,
)


class QualityRanker:
    """Score cleaned answers; never promote garbage into training."""

    def score_one(self, task: str, text: str, *, common_points: list[str] | None = None) -> dict[str, Any]:
        raw = (text or "").strip()
        reasons: list[str] = []
        score = 0.0
        if len(raw) < 80:
            reasons.append("too_short")
            return {"score": 0.05, "pass": False, "reasons": reasons}
        if _BAD.search(raw):
            reasons.append("unsafe_or_garbage")
            return {"score": 0.0, "pass": False, "reasons": reasons}

        # Length sweet spot
        n = len(raw)
        if 200 <= n <= 6000:
            score += 0.25
        elif n > 80:
            score += 0.12
        else:
            reasons.append("thin")

        # Structure
        if re.search(r"(^|\n)\s*([-*•]|\d+[.)])\s+", raw):
            score += 0.15
            reasons.append("has_list")
        if re.search(r"\b(architecture|design|step|trade-?off|recommend)\b", raw, re.I):
            score += 0.1
        if re.search(r"```|`[^`]+`", raw):
            score += 0.08
            reasons.append("has_code")

        # Coverage vs common points
        common = common_points or []
        if common:
            low = raw.lower()
            hit = sum(1 for c in common if c in low)
            cov = hit / max(1, len(common))
            score += 0.25 * cov
            reasons.append(f"coverage_{hit}/{len(common)}")
        else:
            score += 0.1

        # Slight penalty for mock banners in production sense (still usable for pipeline tests)
        if raw.startswith("[") and "mock teacher" in raw.lower():
            score *= 0.85
            reasons.append("mock_source")

        score = max(0.0, min(1.0, score))
        passed = score >= 0.45 and "unsafe_or_garbage" not in reasons
        return {"score": round(score, 3), "pass": passed, "reasons": reasons}

    def rank(
        self,
        task: str,
        responses: list[dict[str, Any]],
        *,
        common_points: list[str] | None = None,
    ) -> dict[str, Any]:
        ranked: list[dict[str, Any]] = []
        for r in responses:
            text = str(r.get("cleaned") or r.get("text") or "").strip()
            if not r.get("ok") or not text:
                continue
            s = self.score_one(task, text, common_points=common_points)
            ranked.append(
                {
                    "provider": r.get("provider"),
                    "model": r.get("model"),
                    "source": r.get("source"),
                    "text": text,
                    "score": s["score"],
                    "pass": s["pass"],
                    "reasons": s["reasons"],
                }
            )
        ranked.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
        winners = [x for x in ranked if x.get("pass")]
        best = winners[0] if winners else (ranked[0] if ranked else None)
        rejected = [x for x in ranked if best and x is not best and float(x.get("score") or 0) + 0.08 < float(best.get("score") or 0)]
        return {
            "ranked": ranked,
            "best": best,
            "rejected_candidates": rejected[:3],
            "pass_count": len(winners),
        }
