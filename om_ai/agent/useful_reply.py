"""Useful assistant replies when the tiny model fails (not static bridge text)."""
from __future__ import annotations

import re


def _python_starter(question: str) -> str:
    q = (question or "").lower()
    if re.search(r"\b(login|sign\s*in|auth)\b", q):
        return '''```python
# login_example.py
def login(username: str, password: str) -> dict:
    if not username or not password:
        return {"ok": False, "error": "username and password required"}
    if len(password) < 8:
        return {"ok": False, "error": "password too short"}
    # TODO: check against your user store / API
    return {"ok": True, "user": username}


if __name__ == "__main__":
    print(login("alice", "secret123"))
```'''
    if re.search(r"\b(api|fastapi|flask|endpoint)\b", q):
        return '''```python
# app.py — FastAPI hello API
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="OM demo API")


class Echo(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/echo")
def echo(body: Echo):
    return {"echo": body.text}


# Run: uvicorn app:app --reload
```'''
    if re.search(r"\b(analy[sz]e|analysis|pandas|csv|data)\b", q):
        return '''```python
# analyze_csv.py — quick data peek
import csv
from collections import Counter
from pathlib import Path


def analyze(path: str) -> None:
    rows = list(csv.DictReader(Path(path).open(newline="", encoding="utf-8")))
    if not rows:
        print("No rows")
        return
    print(f"rows={len(rows)} columns={list(rows[0])}")
    for col in rows[0]:
        values = [r.get(col) or "" for r in rows]
        top = Counter(values).most_common(5)
        print(f"\\n{col}: unique={len(set(values))} top={top}")


if __name__ == "__main__":
    analyze("data.csv")
```'''
    if re.search(r"\b(dashboard|dashbaord)\b", q):
        return '''```python
# dashboard_stats.py
from dataclasses import dataclass


@dataclass
class Stats:
    users: int
    active: int
    errors: int

    @property
    def active_rate(self) -> float:
        return (self.active / self.users) if self.users else 0.0


def render(stats: Stats) -> str:
    return (
        f"Users: {stats.users}\\n"
        f"Active: {stats.active} ({stats.active_rate:.0%})\\n"
        f"Errors: {stats.errors}"
    )


if __name__ == "__main__":
    print(render(Stats(users=1200, active=860, errors=3)))
```'''
    # Default useful starter when user asks for Python/code generically
    return '''```python
# main.py — starter script
from __future__ import annotations


def greet(name: str) -> str:
    name = (name or "world").strip() or "world"
    return f"Hello, {name}!"


def main() -> None:
    print(greet("OM"))
    # Add your logic here
    numbers = [1, 2, 3, 4, 5]
    print("sum =", sum(numbers))


if __name__ == "__main__":
    main()
```'''


def python_code_reply(question: str) -> str:
    q = (question or "").strip()
    code = _python_starter(q)
    return (
        f"Here’s working Python you can run for: **{q[:120] or 'your task'}**\n\n"
        f"{code}\n\n"
        "**Run**\n"
        "```bash\npython3 main.py\n```\n\n"
        "Tell me the exact feature (API, login, CSV analysis, CLI, etc.) and I’ll tailor the code."
    )


def om_tool_help_reply(question: str) -> str:
    return (
        "Yes — I can help you run **OM** as your AI tool.\n\n"
        "## What OM is\n"
        "- Local chat at `/chat` (this workspace)\n"
        "- CLI: `om-ai serve`, `om-ai platform build`, `om-ai system check`\n"
        "- Agents, knowledge/RAG, memory, and the enterprise service mesh\n\n"
        "## Quick start\n"
        "1. Keep `om-ai serve --host 127.0.0.1 --port 8080` running\n"
        "2. Open chat and ask for real work (code, plans, debug)\n"
        "3. For platform status: `om-ai platform health`\n\n"
        f"You said: “{question.strip()[:160]}”.\n\n"
        "What do you want next — **write code**, **fix a bug**, **use knowledge**, or **explain a module**?"
    )


def dashboard_reply(question: str) -> str:
    return (
        "Here’s how to reach the OM dashboard / main surfaces:\n\n"
        "1. **Chat workspace** → `http://127.0.0.1:8080/chat`\n"
        "2. Sidebar → **More** → Settings / Profile / Models / Knowledge\n"
        "3. API tokens UI → `/ui/tokens`\n"
        "4. Platform health (CLI) → `om-ai platform health`\n\n"
        "If you meant a **product dashboard** (metrics UI), say whether you want "
        "React pages, FastAPI routes, or both — I’ll generate the code."
    )


def analyze_python_reply(question: str) -> str:
    return (
        "Here’s a concrete way to **analyze Python** (code or data):\n\n"
        "### If you mean *code review*\n"
        "Paste the file and I’ll check bugs, style, and tests.\n\n"
        "### If you mean *data analysis*\n"
        f"{_python_starter('analyze csv python')}\n\n"
        "### Checklist\n"
        "- Run with `python3 -m py_compile yourfile.py`\n"
        "- Add type hints + a small `pytest` test\n"
        "- Avoid secrets in source\n\n"
        f"Ask: “{question.strip()[:140]}” — paste code or a CSV header and I’ll analyze it directly."
    )


def useful_reply_for(question: str, *, intent: str = "chat") -> str | None:
    """Return a substantive reply, or None to keep other fallbacks."""
    q = (question or "").strip()
    if not q:
        return None
    qlow = q.lower()

    if re.search(r"\b(om|ai\s+tool|handle|hanlde)\b", qlow) and re.search(
        r"\b(om|tool|ai)\b", qlow
    ):
        if re.search(r"\b(handle|hanlde|help|use|run|my\s+ai)\b", qlow):
            return om_tool_help_reply(q)

    if re.search(r"\b(dashboard|dashbaord|go\s+to\s+dash)\b", qlow):
        return dashboard_reply(q)

    if re.search(r"\b(analy[sz]e|analysis)\b", qlow) and re.search(
        r"\b(python|paython|payhthon|code)\b", qlow
    ):
        return analyze_python_reply(q)

    if intent in {"coding", "agent"} or re.search(
        r"\b(python|paython|payhthon|code|script|function|api)\b", qlow
    ):
        if re.search(
            r"\b(create|write|make|generate|give|need|want|build|show)\b", qlow
        ) or re.search(r"\b(python|paython|payhthon|code)\b", qlow):
            return python_code_reply(q)

    return None
