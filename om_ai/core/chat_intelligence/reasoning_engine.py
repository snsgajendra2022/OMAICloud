"""Reasoning engine — turn plan + hypotheses into a structured solve pack."""
from __future__ import annotations

from typing import Any, Callable


class ReasoningEngine:
    """
    Produce reasoning traces and actionable solution structure.
    Optional model_generate can deepen reasoning without canned domain essays.
    """

    def reason(
        self,
        message: str,
        *,
        analysis: dict[str, Any] | None = None,
        hypotheses: dict[str, Any] | None = None,
        plan: dict[str, Any] | None = None,
        knowledge: dict[str, Any] | None = None,
        model_generate: Callable[..., str] | None = None,
    ) -> dict[str, Any]:
        analysis = dict(analysis or {})
        hypotheses = dict(hypotheses or {})
        plan = dict(plan or {})
        knowledge = dict(knowledge or {})

        top = hypotheses.get("top") or {}
        steps = list(plan.get("steps") or [])
        ptype = str(analysis.get("problem_type") or "general")
        domain = str(analysis.get("domain") or "general")
        missing = list(plan.get("missing_information") or analysis.get("missing_information") or [])

        checks = self._checks(ptype, domain, message)
        fix_order = self._fix_order(ptype, top.get("claim") or "", missing)
        approach = str(top.get("claim") or f"Solve as {ptype} in {domain}")

        model_trace = ""
        if model_generate and analysis.get("complexity") == "heavy":
            try:
                prompt = (
                    f"Reason briefly (4 bullets) how to solve:\n{message}\n"
                    f"Leading hypothesis: {approach}\n"
                    f"Plan steps: {', '.join(steps)}"
                )
                model_trace = str(model_generate(prompt) or "").strip()[:1200]
            except Exception:
                model_trace = ""

        return {
            "approach": approach,
            "steps": steps,
            "checks": checks,
            "fix_order": fix_order,
            "missing_information": missing,
            "knowledge_used": bool(knowledge),
            "model_trace": model_trace,
            "problem_type": ptype,
            "domain": domain,
            "rationale": (
                f"Lead with highest-prior hypothesis, run checks, then apply fixes in order."
                if ptype == "debugging"
                else f"Follow {ptype} plan with verification at the end."
            ),
        }

    def _checks(self, ptype: str, domain: str, message: str) -> list[str]:
        if ptype == "debugging":
            base = [
                "Reproduce once and capture the exact failure signal",
                "Note what changed immediately before the break",
                "Isolate the smallest failing unit",
            ]
            if domain == "frontend":
                base.insert(0, "Open DevTools Console and copy the first red error")
            elif domain in {"python", "backend"}:
                base.insert(0, "Read the full traceback and fix the topmost app frame")
            return base
        if ptype == "coding":
            return [
                "Confirm required inputs/outputs",
                "Implement the happy path only first",
                "Add one failure-case test",
            ]
        if ptype == "howto":
            return ["Confirm success criteria", "List prerequisites", "Execute then verify"]
        return ["Confirm the goal", "Give a direct answer", "Offer one next step"]

    def _fix_order(self, ptype: str, claim: str, missing: list[str]) -> list[str]:
        if ptype == "debugging":
            lines = [
                f"Test the leading cause: {claim}" if claim else "Test the most likely cause first",
                "Apply the smallest fix that addresses that cause",
                "Re-run to confirm the failure is gone before changing more",
            ]
            if missing:
                lines.insert(0, f"Gather missing signal: {', '.join(missing)}")
            return lines
        if ptype == "coding":
            return [
                "Write the minimal working version",
                "Handle edge cases",
                "Add a quick verification test",
            ]
        return ["Execute the plan steps in order", "Verify the outcome"]
