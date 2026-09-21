"""Hypothesis engine — candidate causes / approaches before committing."""
from __future__ import annotations

from typing import Any


class HypothesisEngine:
    """Generate ranked hypotheses from problem analysis (dynamic composition)."""

    def generate(
        self,
        message: str,
        *,
        analysis: dict[str, Any] | None = None,
        memory_hits: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        analysis = dict(analysis or {})
        ptype = str(analysis.get("problem_type") or "general")
        domain = str(analysis.get("domain") or "general")
        missing = list(analysis.get("missing_information") or [])
        hyps: list[dict[str, Any]] = []

        if ptype == "debugging":
            hyps = [
                {"id": "h1", "claim": "Recent change introduced a regression", "prior": 0.55},
                {"id": "h2", "claim": "Environment / dependency mismatch", "prior": 0.42},
                {"id": "h3", "claim": "Incorrect configuration or wiring", "prior": 0.48},
                {"id": "h4", "claim": "Unhandled edge-case input", "prior": 0.35},
            ]
            if domain == "frontend":
                hyps.insert(
                    0,
                    {
                        "id": "h0",
                        "claim": "Runtime JS error preventing root render",
                        "prior": 0.62,
                    },
                )
            if "exact_error_text" in missing:
                for h in hyps:
                    h["prior"] = round(float(h["prior"]) * 0.85, 3)
        elif ptype == "coding":
            hyps = [
                {"id": "h1", "claim": "Smallest working slice first, then harden", "prior": 0.7},
                {"id": "h2", "claim": "Reuse existing library / pattern", "prior": 0.5},
            ]
        elif ptype == "howto":
            hyps = [
                {"id": "h1", "claim": "Linear prerequisites → execute → verify", "prior": 0.68},
            ]
        elif ptype == "comparison":
            hyps = [
                {"id": "h1", "claim": "Decide by constraints (team, scale, deadline)", "prior": 0.66},
            ]
        elif ptype == "explanation":
            hyps = [
                {"id": "h1", "claim": "Define → why it matters → concrete example", "prior": 0.7},
            ]
        else:
            hyps = [
                {"id": "h1", "claim": "Clarify goal, then give a direct actionable answer", "prior": 0.6},
            ]

        # Boost hypotheses that match prior successful solutions
        for hit in memory_hits or []:
            kind = str(hit.get("problem_type") or "")
            if kind and kind == ptype:
                for h in hyps[:2]:
                    h["prior"] = round(min(0.95, float(h["prior"]) + 0.08), 3)

        hyps.sort(key=lambda h: float(h.get("prior") or 0), reverse=True)
        return {
            "hypotheses": hyps[:5],
            "top": hyps[0] if hyps else None,
            "count": len(hyps),
            "message_preview": (message or "")[:120],
        }
