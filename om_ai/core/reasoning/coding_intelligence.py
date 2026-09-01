"""Coding Intelligence — senior-architect path, not random snippets.

Requirement → technology → architecture → files → config → install → tests → deploy.

Does not emit canned HTML/JSX unless OM_STATIC_TEMPLATES=1.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any


def _static_ok() -> bool:
    return os.environ.get("OM_STATIC_TEMPLATES", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@dataclass
class CodingBlueprint:
    requirement: str
    architecture: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    layers: list[str] = field(default_factory=list)
    file_structure: list[str] = field(default_factory=list)
    configuration: list[str] = field(default_factory=list)
    installation: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    deployment: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    markdown: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement": self.requirement,
            "architecture": self.architecture,
            "technologies": self.technologies,
            "layers": self.layers,
            "file_structure": self.file_structure,
            "configuration": self.configuration,
            "installation": self.installation,
            "tests": self.tests,
            "deployment": self.deployment,
            "notes": self.notes,
            "markdown": self.markdown,
            "meta": self.meta,
        }


_LOGIN = re.compile(r"\b(login|sign\s*in|sign\s*up|auth|register)\b", re.I)
_PAGE = re.compile(r"\b(page|screen|ui|component)\b", re.I)
_APP = re.compile(r"\b(app|application|system|full.?stack|project)\b", re.I)
_DASH = re.compile(r"\bdashboard\b", re.I)
_PROJECT = re.compile(r"\b(create|make|build|new)\b.*\b(project|app|system|dashboard)\b", re.I)
_API = re.compile(r"\bapi\b", re.I)

_STACK: list[tuple[str, str]] = [
    ("next", "Next.js"),
    ("react", "React"),
    ("vue", "Vue"),
    ("angular", "Angular"),
    ("fastapi", "FastAPI"),
    ("django", "Django"),
    ("flask", "Flask"),
    ("laravel", "Laravel"),
    ("spring", "Spring Boot"),
    (".net", ".NET"),
    ("express", "Express"),
    ("node", "Node.js"),
    ("typescript", "TypeScript"),
    ("javascript", "JavaScript"),
    ("python", "Python"),
    ("java", "Java"),
    ("php", "PHP"),
    ("golang", "Go"),
    (" rust", "Rust"),
    ("c#", "C#"),
    ("csharp", "C#"),
    ("postgres", "PostgreSQL"),
    ("mysql", "MySQL"),
    ("mongodb", "MongoDB"),
    ("redis", "Redis"),
    ("docker", "Docker"),
]


def _stack(text: str) -> list[str]:
    t = f" {(text or '').lower()} "
    found: list[str] = []
    for key, label in _STACK:
        needle = key if key.startswith(" ") or key.startswith(".") else f" {key}"
        if needle in t or f"{key}" in t.replace(".", " "):
            if label not in found:
                found.append(label)
    # avoid tagging Java from JavaScript
    if "Java" in found and "JavaScript" in found:
        found = [x for x in found if x != "Java"]
    return found


def is_coding_ask(text: str) -> bool:
    t = (text or "").lower()
    return bool(
        re.search(
            r"\b(code|implement|react|login|signup|api|page|app|dashboard|"
            r"docker|component|frontend|backend|project|laravel|fastapi|"
            r"typescript|python|java|golang|rust)\b",
            t,
        )
    )


def is_project_ask(text: str) -> bool:
    return bool(_PROJECT.search(text or "") or _DASH.search(text or "") or _APP.search(text or ""))


def _files_for(kind: str, techs: list[str]) -> list[str]:
    frontend = any(t in techs for t in ("React", "Next.js", "Vue", "Angular", "TypeScript", "JavaScript"))
    python_api = any(t in techs for t in ("FastAPI", "Django", "Flask", "Python"))
    php = any(t in techs for t in ("Laravel", "PHP"))
    files: list[str] = []
    if frontend and "Next.js" in techs:
        files += ["app/page.tsx", "app/layout.tsx", "components/", "lib/api.ts", ".env.example"]
    elif frontend:
        files += ["src/App.tsx", "src/pages/", "src/components/", "src/lib/api.ts", "package.json"]
    if python_api:
        files += ["app/main.py", "app/routers/", "app/models.py", "app/schemas.py", "app/auth.py", "requirements.txt", "tests/"]
    if kind == "python_api":
        files = [
            "app/main.py",
            "app/routers/",
            "app/models.py",
            "app/schemas.py",
            "app/deps.py",
            "tests/test_health.py",
            "requirements.txt",
            ".env.example",
            "Dockerfile",
        ]
    if php:
        files += ["app/Http/Controllers/", "routes/api.php", "database/migrations/", "composer.json"]
    if "Docker" in techs or kind in {"full_login_system", "project", "dashboard"}:
        files += ["Dockerfile", "docker-compose.yml"]
    if not files:
        files = ["README.md", "src/", "tests/", ".env.example"]
    return files


def _install_for(techs: list[str]) -> list[str]:
    steps: list[str] = []
    if any(t in techs for t in ("React", "Next.js", "Vue", "Angular", "TypeScript", "JavaScript", "Node.js", "Express")):
        steps.append("Node 20+: `npm install` then `npm run dev`")
    if any(t in techs for t in ("FastAPI", "Django", "Flask", "Python")):
        steps.append("Python 3.11+: `python -m venv .venv && pip install -r requirements.txt`")
        if "FastAPI" in techs:
            steps.append("API: `uvicorn app.main:app --reload`")
    if any(t in techs for t in ("Laravel", "PHP")):
        steps.append("PHP 8.2+: `composer install && php artisan migrate && php artisan serve`")
    if "Docker" in techs:
        steps.append("Container: `docker compose up --build`")
    if not steps:
        steps.append("Use the project's documented package manager; do not invent a new stack.")
    return steps


def build_coding_blueprint(question: str, *, canonical: str = "") -> CodingBlueprint | None:
    q = (question or "").strip()
    if not is_coding_ask(q):
        return None
    stack = _stack(q)
    login = bool(_LOGIN.search(q))
    page_only = bool(_PAGE.search(q)) and not _APP.search(q) and not _DASH.search(q)
    dashboard = bool(_DASH.search(q))
    project = is_project_ask(q) and not page_only
    has_api = bool(_API.search(q))
    frontend = any(t in stack for t in ("React", "Next.js", "Vue", "Angular"))
    python_backend = any(t in stack for t in ("Python", "FastAPI", "Django", "Flask"))
    req = canonical or q[:200]

    if python_backend and not frontend and not login and not dashboard and (has_api or project):
        layers = ["HTTP API", "Schemas/models", "Persistence", "Auth (optional)", "Tests", "Deploy"]
        arch = [
            "ASGI API (FastAPI unless Django/Flask is stated)",
            "Router per resource with Pydantic request/response models",
            "Config and secrets from environment",
            "Health endpoint plus one real resource",
            "Automated tests for happy path and validation errors",
        ]
        techs = list(stack)
        if "FastAPI" not in techs and "Django" not in techs and "Flask" not in techs:
            techs = ["Python", "FastAPI"] + [t for t in techs if t != "Python"]
        if "Python" not in techs:
            techs.insert(0, "Python")
        tests = [
            "GET /health returns 200",
            "Invalid payload is rejected",
            "Auth required routes fail without a token",
        ]
        deploy = ["Uvicorn/Gunicorn behind TLS", "Migrate DB", "Do not commit secrets"]
        notes = [
            "Backend API project — not a React dashboard.",
            "Important: Do not expose API keys.",
        ]
        kind = "python_api"
        config = ["DATABASE_URL from env", "SECRET_KEY from env", "CORS allow-list"]
    elif login and not page_only:
        layers = [
            "Frontend auth UI",
            "Backend API",
            "Database",
            "Authentication",
            "Security",
            "Validation",
        ]
        arch = [
            "Client: login form + session handling",
            "API: POST /login, POST /logout, GET /me",
            "Store: users table with hashed passwords",
            "Guards: HTTPS, rate limit, CSRF/SameSite cookies",
        ]
        techs = stack or ["Frontend", "Backend API", "PostgreSQL"]
        tests = [
            "Reject empty username/password",
            "Reject wrong password without leaking which field failed",
            "Issue session only after successful verify",
        ]
        deploy = ["Env secrets (never commit keys)", "Migrate DB", "TLS in production"]
        notes = [
            "Not a single HTML file — login is a system (UI + API + store + security).",
            "Important: Do not expose API keys or store plaintext passwords.",
        ]
        kind = "full_login_system"
        config = ["AUTH_SECRET from env", "DATABASE_URL from env", "CORS allow-list"]
    elif dashboard or (project and not login):
        layers = ["Layout", "Components", "State", "Charts/data views", "CSS", "API integration"]
        arch = [
            "App shell (nav + content)",
            "Dashboard widgets bound to API data",
            "Client state for filters",
            "Auth gate if the data is private",
        ]
        techs = stack or ["React"]
        tests = ["Empty data state", "API failure", "Responsive layout"]
        deploy = ["CDN or SSR host", "API CORS and auth"]
        notes = ["Skip framework history — ship layout, state, charts, CSS, and API wiring."]
        kind = "dashboard" if dashboard else "project"
        config = ["VITE_API_URL or NEXT_PUBLIC_API_URL from env"]
    elif login and page_only:
        layers = ["Frontend UI", "Form validation", "Auth API client", "Error states"]
        arch = [
            "Login screen component",
            "Client validation",
            "Call backend auth endpoint",
            "Loading / error / success states",
        ]
        techs = stack or ["React"]
        tests = ["Invalid email", "Short password", "API error rendering"]
        deploy = ["Bundle the page", "API base URL via env"]
        notes = ["UI-first, still wired to a real auth API."]
        kind = "login_page"
        config = ["API base URL from env"]
    else:
        layers = ["Requirements", "Architecture", "Implementation", "Tests", "Deploy"]
        arch = ["Clarify interfaces", "Minimal complete slice", "Verify"]
        techs = stack or ["project stack"]
        tests = ["Happy path", "Failure path"]
        deploy = ["Review env and secrets"]
        notes = ["Match the repo stack; do not invent a new framework."]
        kind = "generic"
        config = ["Document required env vars in .env.example"]

    files = _files_for(kind, techs)
    install = _install_for(techs)
    md_lines = [
        f"**Requirement:** {req}",
        "",
        "## Understanding",
        req,
        "",
        "## Architecture",
        *[f"- {a}" for a in arch],
        "",
        "## Technology",
        *[f"- {t}" for t in techs],
        "",
        "## File structure",
        *[f"- `{f}`" for f in files],
        "",
        "## Configuration",
        *[f"- {c}" for c in config],
        "",
        "## Installation",
        *[f"- {s}" for s in install],
        "",
        "## Testing",
        *[f"- {t}" for t in tests],
        "",
        "## Deployment",
        *[f"- {d}" for d in deploy],
        "",
        "## Production improvements",
        "- Observability (logs, traces, error budget)",
        "- Rate limits and auth on public APIs",
        "- **Important:** Do not expose API keys.",
        "",
        "## Notes",
        *[f"- {n}" for n in notes],
    ]

    return CodingBlueprint(
        requirement=req,
        architecture=arch,
        technologies=techs,
        layers=layers,
        file_structure=files,
        configuration=config,
        installation=install,
        tests=tests,
        deployment=deploy,
        notes=notes,
        markdown="\n".join(md_lines).strip() + "\n",
        meta={
            "kind": kind,
            "task_type": (
                "backend"
                if kind == "python_api"
                else "frontend"
                if kind in {"login_page", "dashboard"}
                else "fullstack"
                if kind == "full_login_system"
                else "software"
            ),
            "static_templates": _static_ok(),
            "project_mode": kind
            in {"project", "dashboard", "full_login_system", "python_api"},
        },
    )
