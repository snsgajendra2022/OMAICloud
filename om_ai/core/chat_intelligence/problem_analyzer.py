"""Problem analyzer — understand the user's ask before solving."""
from __future__ import annotations

import re
from typing import Any


class ProblemAnalyzer:
    """
    Dynamic problem framing:
      goal, domain, problem_type, constraints, missing_info, complexity
    """

    _DOMAIN_HINTS: list[tuple[str, re.Pattern[str]]] = [
        ("frontend", re.compile(r"(?i)\b(react|vue|angular|css|html|dom|blank\s+page|ui|jsx|tsx)\b")),
        ("backend", re.compile(r"(?i)\b(api|fastapi|django|flask|server|endpoint|http|rest)\b")),
        ("python", re.compile(r"(?i)\b(python|traceback|pip|venv|django|fastapi)\b")),
        ("devops", re.compile(r"(?i)\b(docker|k8s|kubernetes|deploy|ci|cd|nginx|server)\b")),
        ("data", re.compile(r"(?i)\b(sql|database|postgres|mongo|etl|pandas)\b")),
        ("ml", re.compile(r"(?i)\b(model|train|llm|neural|dataset|inference)\b")),
        ("mobile", re.compile(r"(?i)\b(ios|android|flutter|react\s*native)\b")),
    ]

    def analyze(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        q = (message or "").strip()
        low = q.lower()
        plan = dict(plan or {})
        context = dict(context or {})

        domain = "general"
        for name, pat in self._DOMAIN_HINTS:
            if pat.search(q):
                domain = name
                break

        problem_type = self._problem_type(low, plan)
        goal = self._goal(q, problem_type)
        missing = self._missing_info(low, problem_type)
        constraints = self._constraints(q)
        complexity = self._complexity(q, problem_type, missing)

        confidence = 0.72
        if missing:
            confidence -= 0.08 * min(3, len(missing))
        if problem_type == "unknown":
            confidence = min(confidence, 0.45)
        if plan.get("strategy"):
            confidence = min(0.92, confidence + 0.08)

        return {
            "goal": goal,
            "domain": domain or str(plan.get("domain") or "general"),
            "problem_type": problem_type,
            "constraints": constraints,
            "missing_information": missing,
            "complexity": complexity,
            "confidence": round(max(0.2, min(0.95, confidence)), 3),
            "strategy_hint": str(plan.get("strategy") or ""),
            "followup": bool(context.get("followup")),
            "raw_preview": q[:240],
        }

    def _problem_type(self, low: str, plan: dict[str, Any]) -> str:
        strat = str(plan.get("strategy") or "")
        if strat == "technical_solution" or re.search(
            r"\b(error|bug|crash|broken|exception|not working|blank page)\b", low
        ):
            return "debugging"
        if strat == "code_solution" or re.search(r"\b(code|implement|function|script|write)\b", low):
            return "coding"
        if strat == "step_by_step" or re.search(r"\b(how (do|to)|steps?|guide)\b", low):
            return "howto"
        if strat == "comparison" or re.search(r"\b(vs|versus|compare|which is better)\b", low):
            return "comparison"
        if strat == "explanation" or re.search(r"\b(what is|explain|define|why)\b", low):
            return "explanation"
        if re.search(r"\b(design|architect|system design)\b", low):
            return "design"
        return "general"

    def _goal(self, q: str, problem_type: str) -> str:
        cleaned = re.sub(r"\s+", " ", (q or "").strip())
        if len(cleaned) > 160:
            cleaned = cleaned[:157] + "..."
        verbs = {
            "debugging": "Fix",
            "coding": "Implement",
            "howto": "Accomplish",
            "comparison": "Choose",
            "explanation": "Understand",
            "design": "Design",
        }
        return f"{verbs.get(problem_type, 'Solve')}: {cleaned or 'user request'}"

    def _missing_info(self, low: str, problem_type: str) -> list[str]:
        missing: list[str] = []
        if problem_type == "debugging":
            if not re.search(r"(error|traceback|exception|console|log|status\s*\d{3})", low):
                missing.append("exact_error_text")
            if not re.search(r"(react|python|node|java|go|rust|django|fastapi)", low):
                missing.append("stack_or_runtime")
        if problem_type == "coding" and not re.search(r"(python|js|typescript|react|api)", low):
            missing.append("language_or_stack")
        if problem_type == "comparison":
            opts = re.findall(r"\b([A-Za-z][\w.+#-]{1,24})\s+vs\.?\s+([A-Za-z][\w.+#-]{1,24})\b", low)
            if not opts:
                missing.append("options_to_compare")
        return missing

    def _constraints(self, q: str) -> list[str]:
        found: list[str] = []
        low = q.lower()
        for label, pat in (
            ("deadline", r"\b(today|asap|urgent|deadline|by\s+friday)\b"),
            ("production", r"\b(production|prod|live|customers)\b"),
            ("beginner", r"\b(beginner|simple|eli5|explain like)\b"),
            ("performance", r"\b(fast|latency|scale|performance)\b"),
        ):
            if re.search(pat, low):
                found.append(label)
        return found

    def _complexity(self, q: str, problem_type: str, missing: list[str]) -> str:
        words = len(re.findall(r"\w+", q or ""))
        if problem_type in {"design"} or words > 80:
            return "heavy"
        if missing or problem_type in {"debugging", "coding"}:
            return "normal"
        if words < 10:
            return "light"
        return "normal"
