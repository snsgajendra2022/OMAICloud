"""Solution engine — deterministic problem-solving scaffolds."""
from __future__ import annotations

import re
from typing import Any


class SolutionEngine:
    """Produce structured solutions for debugging / howto / coding asks."""

    def solve(
        self,
        message: str,
        *,
        plan: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = dict(plan or {})
        strategy = str(plan.get("strategy") or "")
        q = (message or "").strip()
        low = q.lower()

        if strategy == "technical_solution" or self._is_debug(low):
            return self._debug_solution(q, low, plan)
        if strategy == "code_solution":
            return self._code_solution(q, low, plan)
        if strategy == "step_by_step":
            return self._howto_solution(q, plan)
        if strategy == "comparison":
            return self._compare_solution(q, plan)
        if strategy == "explanation":
            # Never dump static concept template for personal questions
            if re.search(r"(?i)\b(my\s+name|mera\s+naam|who\s+am\s+i)\b", q):
                return {"solved": False, "answer": "", "kind": "none", "notes": ["personal"]}
            return self._explain_solution(q, plan)

        return {
            "solved": False,
            "answer": "",
            "kind": "none",
            "notes": [],
        }

    def _is_debug(self, low: str) -> bool:
        return bool(
            re.search(
                r"\b(error|bug|blank\s+page|crash|not\s+working|broken|exception)\b",
                low,
            )
        )

    def _debug_solution(self, q: str, low: str, plan: dict[str, Any]) -> dict[str, Any]:
        notes: list[str] = []
        checks: list[str] = []
        fix_lines: list[str] = []

        if "react" in low or "blank page" in low:
            notes.append("A React blank page usually means a runtime JS error or a bad root render.")
            checks = [
                "Open DevTools → Console and copy the first red error.",
                "Confirm `index.js`/`main.jsx` mounts `<App />` into `#root`.",
                "Check that `public/index.html` (or Vite `index.html`) contains `<div id=\"root\"></div>`.",
                "Verify imports/paths (case-sensitive on Linux) and that the component exports correctly.",
                "Temporarily replace App with `return <div>Hello</div>` to isolate the failing component.",
            ]
            fix_lines = [
                "1. Fix the first console error (often undefined variable, bad import, or hooks rule).",
                "2. Ensure the root element id matches `createRoot(document.getElementById('root'))`.",
                "3. Restart the dev server after dependency/config changes.",
                "4. If using React Router, wrap routes in `<BrowserRouter>` and confirm the path exists.",
            ]
            if plan.get("ask_details"):
                fix_lines.append(
                    "If you paste the console error + your `main`/`App` snippet, I can pinpoint the exact fix."
                )
        elif "python" in low:
            notes.append("Python runtime errors are usually import path, exception, or env issues.")
            checks = [
                "Read the full traceback — fix the topmost frame that is your code.",
                "Confirm virtualenv is active and dependencies are installed.",
                "Check file paths and package `__init__` layout.",
            ]
            fix_lines = [
                "1. Address the exception type/message in the traceback.",
                "2. Add a minimal reproduction (10–20 lines) around the failing call.",
                "3. Re-run after each change to confirm progress.",
            ]
        else:
            notes.append("Let's troubleshoot systematically.")
            checks = [
                "Reproduce the issue once and note exact steps.",
                "Capture the full error message / logs.",
                "Identify what changed right before it broke.",
                "Test a minimal version of the failing part.",
            ]
            fix_lines = [
                "1. Share the exact error text if you have it.",
                "2. Check the most recent change first.",
                "3. Apply a small isolated fix, then retest.",
            ]

        answer_parts = []
        if notes:
            answer_parts.append(notes[0])
        answer_parts.append("\n**Quick checks**")
        answer_parts.extend(f"- {c}" for c in checks)
        answer_parts.append("\n**Fix plan**")
        answer_parts.extend(fix_lines)
        answer = "\n".join(answer_parts).strip()

        return {
            "solved": True,
            "answer": answer,
            "kind": "debugging",
            "notes": notes,
            "checks": checks,
            "complete": not bool(plan.get("ask_details")),
        }

    def _code_solution(self, q: str, low: str, plan: dict[str, Any]) -> dict[str, Any]:
        answer = (
            f"Here's a practical approach for: {q}\n\n"
            "1. Clarify the exact input/output you need.\n"
            "2. Implement the smallest working version first.\n"
            "3. Add error handling and edge cases.\n"
            "4. Test with one happy-path and one failure case.\n\n"
            "Tell me your stack (e.g. React/Python) and constraints if you want a concrete snippet."
        )
        return {"solved": True, "answer": answer, "kind": "coding", "complete": False}

    def _howto_solution(self, q: str, plan: dict[str, Any]) -> dict[str, Any]:
        answer = (
            f"Here's a step-by-step plan for: {q}\n\n"
            "1. Define the goal and success criteria.\n"
            "2. Prepare prerequisites (tools, access, files).\n"
            "3. Execute the core steps in order.\n"
            "4. Verify the result.\n"
            "5. Note follow-ups / cleanup.\n\n"
            "I can expand any step into exact commands or code — say which step you want first."
        )
        return {"solved": True, "answer": answer, "kind": "howto", "complete": True}

    def _compare_solution(self, q: str, plan: dict[str, Any]) -> dict[str, Any]:
        answer = (
            f"Comparison for: {q}\n\n"
            "**How to decide**\n"
            "- Goal / workload\n"
            "- Complexity & learning cost\n"
            "- Ecosystem & hiring\n"
            "- Performance / ops needs\n\n"
            "Share the two options and your constraints (team size, deadline, scale) "
            "and I’ll recommend one clearly."
        )
        return {"solved": True, "answer": answer, "kind": "comparison", "complete": False}

    def _explain_solution(self, q: str, plan: dict[str, Any]) -> dict[str, Any]:
        topic = re.sub(r"^(what\s+is|explain|define)\s+", "", q, flags=re.I).strip(" ?")
        answer = (
            f"**{topic or 'Concept'}** — plain-language explanation\n\n"
            f"{topic or 'This'} is best understood by: (1) what it is, "
            "(2) why people use it, (3) a simple example.\n\n"
            "Ask for a deeper dive, analogy, or code sample if you want more."
        )
        return {"solved": True, "answer": answer, "kind": "explanation", "complete": False}
