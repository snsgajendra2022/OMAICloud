"""Compare teacher answers and extract shared / unique points."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

# Lightweight topic cues used for overlap (not a full NLP stack).
_CUES = (
    "isolation",
    "middleware",
    "database",
    "permission",
    "auth",
    "queue",
    "cache",
    "security",
    "scalability",
    "tenant",
    "api",
    "observability",
    "testing",
    "deployment",
    "architecture",
    "storage",
    "network",
    "policy",
    "audit",
    "encryption",
    # software / frontend
    "component",
    "hooks",
    "state",
    "props",
    "jsx",
    "react",
    "routing",
    # devops
    "kubernetes",
    "pod",
    "deployment",
    "service",
    "ingress",
    "cluster",
)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    out = []
    for p in parts:
        s = re.sub(r"\s+", " ", p).strip(" -•*\t")
        if len(s) >= 24:
            out.append(s)
    return out


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", (text or "").lower()) if t}


class AnswerComparator:
    """Find common themes and disagreements across teacher responses."""

    def compare(self, task: str, responses: list[dict[str, Any]]) -> dict[str, Any]:
        usable = [r for r in responses if r.get("ok") and str(r.get("text") or "").strip()]
        cue_hits: Counter[str] = Counter()
        per_provider: dict[str, list[str]] = {}
        for r in usable:
            text = str(r.get("text") or "")
            low = text.lower()
            found = [c for c in _CUES if c in low]
            cue_hits.update(found)
            per_provider[str(r.get("provider") or "?")] = found
            for sent in _sentences(text)[:12]:
                for c in _CUES:
                    if c in sent.lower():
                        cue_hits[c] += 1

        n = max(1, len(usable))
        common = [c for c, k in cue_hits.most_common(20) if k >= max(2, n // 2 + (1 if n > 1 else 0))]
        if not common and cue_hits:
            common = [c for c, _ in cue_hits.most_common(5)]

        # Unique emphasis per teacher
        unique: dict[str, list[str]] = {}
        common_set = set(common)
        for pid, found in per_provider.items():
            uniq = [c for c in found if c not in common_set]
            if uniq:
                unique[pid] = sorted(set(uniq))

        # Token overlap between top answers
        overlaps: list[dict[str, Any]] = []
        texts = [(str(r.get("provider")), _tokens(str(r.get("text") or ""))) for r in usable]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, ta = texts[i]
                b, tb = texts[j]
                if not ta or not tb:
                    continue
                inter = len(ta & tb)
                union = len(ta | tb) or 1
                overlaps.append(
                    {
                        "a": a,
                        "b": b,
                        "jaccard": round(inter / union, 3),
                    }
                )

        return {
            "task": task,
            "common_points": common,
            "cue_counts": dict(cue_hits.most_common(30)),
            "unique_points": unique,
            "pairwise_overlap": overlaps,
            "teacher_count": len(usable),
        }
