"""
Result Analysis — decide if tool output is enough to answer, or retry/clarify.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionAnalysis:
    sufficient: bool
    summary: str
    used_tools: list[str] = field(default_factory=list)
    failed_tools: list[str] = field(default_factory=list)
    next_action: str = "respond"  # respond | retry | clarify | escalate
    confidence: float = 0.5
    highlights: list[str] = field(default_factory=list)


class ResultAnalyzer:
    def analyze(
        self,
        question: str,
        execution: dict[str, Any],
        *,
        decision_mode: str = "answer",
    ) -> ActionAnalysis:
        results = list(execution.get("results") or [])
        used = [str(r.get("tool")) for r in results if r.get("ok")]
        failed = [str(r.get("tool")) for r in results if not r.get("ok")]
        combined = str(execution.get("combined_text") or "").strip()
        highlights: list[str] = []
        for r in results:
            if r.get("ok") and r.get("text"):
                highlights.append(str(r["text"])[:240])

        if not results and decision_mode == "answer":
            return ActionAnalysis(
                sufficient=True,
                summary="No tools needed — answer directly.",
                next_action="respond",
                confidence=0.85,
            )

        if combined and len(combined) >= 40:
            return ActionAnalysis(
                sufficient=True,
                summary=f"Tool results ready ({len(used)} ok, {len(failed)} failed).",
                used_tools=used,
                failed_tools=failed,
                next_action="respond",
                confidence=0.8 if not failed else 0.65,
                highlights=highlights[:4],
            )

        if used and not combined:
            return ActionAnalysis(
                sufficient=False,
                summary="Tools ran but produced little text.",
                used_tools=used,
                failed_tools=failed,
                next_action="clarify",
                confidence=0.4,
            )

        if failed and not used:
            return ActionAnalysis(
                sufficient=False,
                summary="All tools failed or were blocked.",
                failed_tools=failed,
                next_action="respond",  # fall back to model / knowledge
                confidence=0.35,
            )

        return ActionAnalysis(
            sufficient=bool(combined),
            summary="Partial tool coverage.",
            used_tools=used,
            failed_tools=failed,
            next_action="respond",
            confidence=0.55,
            highlights=highlights[:3],
        )
