"""Specialist agents — produce real work products (plans, reviews, schemas), not labels."""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text or "")


def research_agent(goal: str, *, snippets: list[str] | None = None) -> dict[str, Any]:
    from om_ai.knowledge.selector import select_knowledge

    profile = select_knowledge(goal, snippets or [])
    return {
        "agent": "research",
        "topic": profile.topic,
        "important": profile.important,
        "not_important": profile.not_important,
        "kept": profile.kept[:4],
        "markdown": (
            "## Research\n"
            + (f"- Domain: `{profile.topic}`\n" if profile.topic else "")
            + "\n".join(f"- Use: {x}" for x in (profile.important or ["task-relevant sources"])[:6])
            + (
                "\n"
                + "\n".join(f"- Skip: {x}" for x in profile.not_important[:3])
                if profile.not_important
                else ""
            )
        ),
    }


def security_agent(goal: str) -> dict[str, Any]:
    t = (goal or "").lower()
    checks = [
        "Do not commit secrets or API keys",
        "Hash passwords (bcrypt/argon2); never store plaintext",
        "Validate and bound all inputs",
        "Use HTTPS and secure cookie flags in production",
    ]
    if any(w in t for w in ("login", "auth", "signup")):
        checks += [
            "Rate-limit authentication endpoints",
            "Generic error on failed login (no user enumeration)",
            "CSRF protection or SameSite cookies for browser sessions",
        ]
    if "docker" in t:
        checks.append("Run containers as non-root; no secrets in image layers")
    return {
        "agent": "security",
        "checks": checks,
        "markdown": "## Security\n" + "\n".join(f"- {c}" for c in checks),
    }


def database_agent(goal: str) -> dict[str, Any]:
    t = (goal or "").lower()
    tables = ["users"]
    if any(w in t for w in ("login", "auth", "signup")):
        tables = ["users", "sessions"]
    if "dashboard" in t:
        tables += ["metrics_cache"]
    schema = [
        f"{name}: id PK, created_at, updated_at" + (", email UNIQUE, password_hash" if name == "users" else "")
        for name in tables
    ]
    return {
        "agent": "database",
        "tables": tables,
        "markdown": "## Database\n" + "\n".join(f"- `{s}`" for s in schema) + "\n- Index hot lookup columns\n",
    }


def testing_agent(goal: str) -> dict[str, Any]:
    cases = [
        "Happy path of the stated requirement",
        "Invalid / empty input",
        "Unauthorized / forbidden path if auth exists",
        "Failure of a downstream dependency (API/DB down)",
    ]
    if re.search(r"\b(login|auth)\b", goal or "", re.I):
        cases.insert(0, "Wrong password does not leak whether the user exists")
    cmd = "pytest -q" if re.search(r"\b(python|fastapi|django|flask)\b", goal or "", re.I) else "npm test (or project test script)"
    return {
        "agent": "testing",
        "cases": cases,
        "command": cmd,
        "markdown": "## Testing\n" + "\n".join(f"- {c}" for c in cases) + f"\n\nRun: `{cmd}`\n",
    }


def deployment_agent(goal: str) -> dict[str, Any]:
    steps = [
        "Set secrets via environment (never bake into images)",
        "Health check endpoint before traffic",
        "TLS in production",
        "Log without PII",
    ]
    if re.search(r"\bdocker\b", goal or "", re.I) or True:
        steps.insert(0, "Dockerfile: pin base image, multi-stage if compiling, non-root user")
    return {
        "agent": "deployment",
        "steps": steps,
        "markdown": "## Deployment\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1)),
    }


def coding_agent(goal: str, *, canonical: str = "") -> dict[str, Any]:
    from om_ai.core.reasoning.coding_intelligence import build_coding_blueprint

    bp = build_coding_blueprint(goal, canonical=canonical)
    if not bp:
        return {"agent": "coding", "markdown": "", "blueprint": None}
    return {"agent": "coding", "markdown": bp.markdown, "blueprint": bp.to_dict()}


def run_specialists(
    goal: str,
    *,
    agents: list[str],
    snippets: list[str] | None = None,
    canonical: str = "",
) -> dict[str, Any]:
    """Execute named specialists and merge markdown work products."""
    wanted = list(agents or [])
    t = (goal or "").lower()
    if any(w in t for w in ("code", "react", "api", "login", "dashboard", "app", "project")):
        if "coding" not in wanted:
            wanted.append("coding")
        if "testing" not in wanted:
            wanted.append("testing")
        if "security" not in wanted:
            wanted.append("security")
    if any(w in t for w in ("deploy", "docker", "production")) and "deployment" not in wanted:
        wanted.append("deployment")
    if any(w in t for w in ("database", "postgres", "mysql", "mongo", "sql", "login", "auth")):
        if "database" not in wanted:
            wanted.append("database")

    outputs: list[dict[str, Any]] = []
    parts: list[str] = []
    dispatch = {
        "research": lambda: research_agent(goal, snippets=snippets),
        "security": lambda: security_agent(goal),
        "database": lambda: database_agent(goal),
        "testing": lambda: testing_agent(goal),
        "deployment": lambda: deployment_agent(goal),
        "devops": lambda: deployment_agent(goal),
        "coding": lambda: coding_agent(goal, canonical=canonical),
    }
    for name in wanted:
        fn = dispatch.get(name)
        if not fn:
            outputs.append({"agent": name, "markdown": "", "note": "routed"})
            continue
        try:
            item = fn()
        except Exception as exc:
            logger.debug("specialist %s failed: %s", name, exc)
            item = {"agent": name, "markdown": "", "error": str(exc)}
        outputs.append(item)
        md = str(item.get("markdown") or "").strip()
        if md:
            parts.append(md)

    return {
        "agents": wanted,
        "outputs": outputs,
        "markdown": "\n\n".join(parts).strip(),
        "coding_output": next((o.get("markdown") or "" for o in outputs if o.get("agent") == "coding"), ""),
    }
