"""Explanation engine — turn reasoning into a natural solvable answer."""
from __future__ import annotations

from typing import Any, Callable


class ExplanationEngine:
    """Compose human-readable solutions from structured reasoning."""

    def explain(
        self,
        message: str,
        *,
        analysis: dict[str, Any] | None = None,
        reasoning: dict[str, Any] | None = None,
        plan: dict[str, Any] | None = None,
        model_generate: Callable[..., str] | None = None,
    ) -> dict[str, Any]:
        analysis = dict(analysis or {})
        reasoning = dict(reasoning or {})
        plan = dict(plan or {})
        ptype = str(analysis.get("problem_type") or reasoning.get("problem_type") or "general")
        goal = str(analysis.get("goal") or message or "").strip()

        parts: list[str] = []
        approach = str(reasoning.get("approach") or "").strip()
        if approach:
            parts.append(approach if approach.endswith(".") else approach + ".")

        checks = list(reasoning.get("checks") or [])
        fix_order = list(reasoning.get("fix_order") or [])
        missing = list(reasoning.get("missing_information") or plan.get("missing_information") or [])

        if ptype == "debugging":
            if checks:
                parts.append("\n**Quick checks**")
                parts.extend(f"- {c}" for c in checks)
            if fix_order:
                parts.append("\n**Fix plan**")
                parts.extend(f"{i}. {step}" for i, step in enumerate(fix_order, 1))
            if missing and plan.get("ask_details"):
                parts.append(
                    "\nIf you share "
                    + ", ".join(m.replace("_", " ") for m in missing[:3])
                    + ", I can pinpoint the exact fix."
                )
        elif ptype == "coding":
            parts.append(f"Practical approach for: {goal}")
            parts.append("")
            for i, step in enumerate(fix_order or ["Implement a minimal version", "Harden", "Test"], 1):
                parts.append(f"{i}. {step}")
        elif ptype == "howto":
            parts.append(f"Step-by-step for: {goal}")
            parts.append("")
            for i, step in enumerate(list(plan.get("steps") or fix_order) or ["Define goal", "Execute", "Verify"], 1):
                parts.append(f"{i}. {str(step).replace('_', ' ')}")
        elif ptype == "comparison":
            parts.append(f"How to decide for: {goal}")
            parts.append("- Criteria first (team, deadline, scale, ops)")
            parts.append("- Tradeoffs per option")
            parts.append("- Clear recommendation with why")
            if missing:
                parts.append("Tell me the two options and your main constraint.")
        elif ptype == "explanation":
            topic = goal.replace("Understand:", "").strip() or "this"
            parts.append(f"**{topic}** — plain-language take")
            parts.append(
                f"{topic} is clearest as: (1) what it is, (2) why it matters, (3) one concrete example."
            )
            parts.append("Ask for a deeper dive or a code sample if you want more.")
        else:
            parts.append(f"Here's the direct path for: {goal}")
            for i, step in enumerate(list(plan.get("steps") or ["answer", "next_step"]), 1):
                parts.append(f"{i}. {str(step).replace('_', ' ')}")

        if reasoning.get("model_trace"):
            parts.append("\n**Deeper reasoning**")
            parts.append(str(reasoning["model_trace"])[:800])

        answer = "\n".join(p for p in parts if p is not None).strip()

        # Optional model polish — never invent if empty
        if model_generate and len(answer) < 40:
            try:
                polished = str(
                    model_generate(
                        message,
                        f"Write a clear companion solution.\nStructure:\n{answer}",
                    )
                    or ""
                ).strip()
                if len(polished) > len(answer):
                    answer = polished
            except TypeError:
                try:
                    polished = str(model_generate(message) or "").strip()
                    if len(polished) > len(answer):
                        answer = polished
                except Exception:
                    pass
            except Exception:
                pass

        return {
            "answer": answer,
            "kind": ptype if ptype != "general" else "solution",
            "complete": not bool(plan.get("ask_details") and missing),
        }
