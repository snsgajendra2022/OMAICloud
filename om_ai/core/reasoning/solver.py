"""Solution generator with domain-aware outlines and starter artifacts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .analyzer import IntentResult
from .planner import PlanResult


@dataclass
class SolutionResult:
    solution: str
    architecture: list[str] = field(default_factory=list)
    implementation_notes: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "solution": self.solution,
            "architecture": self.architecture,
            "implementation_notes": self.implementation_notes,
            "meta": self.meta,
        }


def _react_login_solution(question: str) -> tuple[str, list[str], list[str]]:
    arch = [
        "src/Login.jsx — form UI + validation",
        "src/Login.css — responsive layout",
        "Optional: auth API client + error states",
    ]
    notes = [
        "Client-side validation before submit",
        "Never store plaintext passwords",
        "Use HTTPS + httpOnly cookies or secure tokens in production",
    ]
    code = '''```jsx
// src/Login.jsx
import { useState } from "react";
import "./Login.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function validate() {
    if (!email.includes("@")) return "Enter a valid email";
    if (password.length < 8) return "Password must be at least 8 characters";
    return "";
  }

  async function onSubmit(e) {
    e.preventDefault();
    const v = validate();
    if (v) { setError(v); return; }
    setError("");
    // TODO: call your auth API
  }

  return (
    <main className="login">
      <h1>Sign in</h1>
      <form onSubmit={onSubmit}>
        <label>Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error ? <p className="error" role="alert">{error}</p> : null}
        <button type="submit">Sign in</button>
      </form>
    </main>
  );
}
```

```css
/* src/Login.css */
.login { max-width: 360px; margin: 4rem auto; padding: 1.5rem; font-family: system-ui, sans-serif; }
.login label { display: block; margin: 0.75rem 0; }
.login input { width: 100%; padding: 0.5rem; margin-top: 0.25rem; }
.login .error { color: #b00020; }
.login button { margin-top: 1rem; width: 100%; padding: 0.65rem; }
@media (max-width: 480px) { .login { margin: 1.5rem; } }
```'''
    solution = (
        f"**Ask:** {question.strip()[:300]}\n\n"
        "## Architecture\n"
        "- Component: `Login.jsx`\n"
        "- Styles: `Login.css`\n"
        "- Features: validation, error handling, responsive layout\n\n"
        "## Implementation\n"
        f"{code}\n\n"
        "## Testing\n"
        "- Empty / invalid email, short password, happy path\n"
        "- Optional React Testing Library smoke for `validate()`\n"
        "- Never commit secrets or hardcode API keys\n\n"
        "## Run\n"
        "```bash\nnpm start\n```\n"
    )
    return solution, arch, notes


def _school_management_solution(question: str) -> tuple[str, list[str], list[str]]:
    arch = [
        "Modules: Students, Teachers, Classes, Attendance, Grades, Auth",
        "API: FastAPI/Nest + PostgreSQL",
        "UI: React admin + role-based dashboards",
        "Integrations: email/SMS notifications (optional)",
    ]
    notes = [
        "RBAC: admin / teacher / student / parent",
        "Audit log for grade changes",
        "Backups + soft deletes for student records",
    ]
    solution = (
        f"**Ask:** {question.strip()[:300]}\n\n"
        "## Analysis\n"
        "A school management system needs multi-role access, reliable records, "
        "and clear workflows for enrollment, attendance, and grading.\n\n"
        "## Architecture\n"
        "1. **Identity** — users, roles, sessions\n"
        "2. **Academic core** — schools → years → classes → subjects\n"
        "3. **People** — students, teachers, parents (linked)\n"
        "4. **Operations** — attendance, assignments, grades, fees\n"
        "5. **Reporting** — exports, dashboards\n\n"
        "## Implementation plan\n"
        "1. Schema + auth\n"
        "2. CRUD for students/classes\n"
        "3. Attendance + grades APIs\n"
        "4. Teacher/admin UI\n"
        "5. Tests + seed data\n\n"
        "## Validation\n"
        "- Role isolation tests\n"
        "- Attendance uniqueness per day/student\n"
        "- Grade audit trail\n"
    )
    return solution, arch, notes


def _generic_coding_solution(question: str, intent: IntentResult, plan: PlanResult) -> tuple[str, list[str], list[str]]:
    arch = [
        "Clarify requirements + acceptance tests",
        "Locate modules / contracts",
        "Minimal change → verify → document",
    ]
    notes = [
        f"Intent={intent.intent} domain={intent.domain}",
        f"Agents: {', '.join(plan.agents)}",
    ]
    steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan.plan))
    solution = (
        f"**Ask:** {question.strip()[:400]}\n\n"
        f"**Understanding:** {intent.understanding}\n\n"
        f"## Plan\n{steps}\n\n"
        "## Implementation approach\n"
        "- Prefer smallest safe change\n"
        "- Add/adjust tests that prove the fix\n"
        "- Note security/privacy implications\n"
    )
    return solution, arch, notes


class SolutionGenerator:
    def solve(
        self,
        question: str,
        intent: IntentResult,
        plan: PlanResult,
        *,
        knowledge_hits: list[str] | None = None,
    ) -> SolutionResult:
        q = (question or "").strip()
        qlow = q.lower()
        hits = knowledge_hits or []

        if re.search(r"\breact\b", qlow) and re.search(r"\b(login|sign\s*in|auth)\b", qlow):
            solution, arch, notes = _react_login_solution(q)
            meta = {"template": "react_login"}
        elif re.search(r"\bschool\b", qlow) and re.search(r"\b(management|sms|erp)\b", qlow):
            solution, arch, notes = _school_management_solution(q)
            meta = {"template": "school_management"}
        elif intent.intent in {"coding", "debug", "architecture"} or intent.domain == "software":
            solution, arch, notes = _generic_coding_solution(q, intent, plan)
            meta = {"template": "coding_generic"}
        else:
            arch = [
                "Understanding",
                "Knowledge retrieval",
                "Planning + agent selection",
                "Implementation",
                "Verification",
            ]
            notes = [
                f"Intent={intent.intent} domain={intent.domain}",
                f"Agents: {', '.join(plan.agents)}",
                "Prefer 2026-current facts; label research horizons",
            ]
            steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan.plan))
            solution = (
                f"**Understanding:** {intent.understanding}\n\n"
                f"## Analysis\n"
                f"Domain `{intent.domain}` · Intent `{intent.intent}`\n\n"
                f"## Plan\n{steps}\n\n"
                f"## Solution approach\n"
                f"Execute the plan with OM tools/agents. "
                f"Use Knowledge Universe when facts are required.\n\n"
                f"**Ask:** {q[:500]}"
            )
            meta = {"template": "general"}

        if hits:
            notes.append(f"Retrieved {len(hits)} knowledge snippets")
            solution += "\n\n## Knowledge context\n" + "\n".join(
                f"- {h[:220]}" for h in hits[:5]
            )
        meta["solver"] = "om-solver-v2"
        return SolutionResult(
            solution=solution,
            architecture=arch,
            implementation_notes=notes,
            meta=meta,
        )
