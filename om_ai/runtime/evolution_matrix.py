"""OM evolution levels L1–L5 for /chat model selection.

Honest contract:
  - L1 (and chat-like turns on any level) use live OM-1.0 native chat.
  - L2–L5 matrix/sandbox/goal-tree only for agentic / numeric / orchestration prompts.
  - Selecting L5 does **not** create Organization AGI.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import os
import re
import sys
from pathlib import Path
from typing import Any

EVOLUTION_MODELS: list[dict[str, Any]] = [
    {
        "id": "OM-L1",
        "name": "OM Level 1 · Chatbot",
        "kind": "evolution",
        "level": 1.0,
        "description": "Fluent chat — live OM-1.0 native + tools.",
        "temperature": 0.7,
        "context_length": 256,
        "max_tokens": 256,
    },
    {
        "id": "OM-L2",
        "name": "OM Level 2 · Reasoner",
        "kind": "evolution",
        "level": 2.0,
        "description": "Chain-of-thought for hard questions; normal chat stays native.",
        "temperature": 0.4,
        "context_length": 256,
        "max_tokens": 320,
    },
    {
        "id": "OM-L3",
        "name": "OM Level 3 · Agent",
        "kind": "evolution",
        "level": 3.0,
        "description": "Sandbox agent for math/code goals; greetings use native chat.",
        "temperature": 0.5,
        "context_length": 256,
        "max_tokens": 320,
    },
    {
        "id": "OM-L4",
        "name": "OM Level 4 · Innovator",
        "kind": "evolution",
        "level": 4.0,
        "description": "Hypothesis scaffold for research-style prompts.",
        "temperature": 0.55,
        "context_length": 256,
        "max_tokens": 320,
    },
    {
        "id": "OM-L5",
        "name": "OM Level 5 · Organization Matrix",
        "kind": "evolution",
        "level": 5.0,
        "description": "Goal-tree matrix for enterprise objectives; normal chat uses OM native.",
        "temperature": 0.5,
        "context_length": 512,
        "max_tokens": 512,
    },
]

_ALIASES = {
    "om-1.0": "OM-L1",
    "om-1": "OM-L1",
    "om smart": "OM-L1",
    "om-l1": "OM-L1",
    "om-l2": "OM-L2",
    "om-reasoning": "OM-L2",
    "om-l3": "OM-L3",
    "om-agent": "OM-L3",
    "om-fast": "OM-L1",
    "om-vision": "OM-L1",
    "om-l4": "OM-L4",
    "om-l5": "OM-L5",
    "om-5.0": "OM-L5",
    "om-5": "OM-L5",
    "om matrix": "OM-L5",
}

_MATRIX_HINT = re.compile(
    r"\b("
    r"orchestrat|objective|enterprise|budget|projection|project costs?|"
    r"multi[- ]?agent|dispatch|sandbox|CODE_EXEC|calculate|compute|"
    r"growth rate|percent|%\s*of|fibonacci|run (a )?script|"
    r"organization|goal tree|autonomous expansion"
    r")\b",
    re.I,
)
_CHATTY = re.compile(
    r"^\s*("
    r"hi+|hello+|hey+|yo+|thanks?|thank you|ok|okay|bye|good\s*(morning|evening|night)|"
    r"how are you|who are you|what('?s| is) (om|the ai|ai|this)|"
    r"what can you (do|help)|help me\??"
    r")[\s!.?]*$",
    re.I,
)


def _ensure_repo_root_on_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    s = str(root)
    if s not in sys.path:
        sys.path.insert(0, s)
    return root


def _load_om5():
    """Import om5_core from repo root (not installed as a package)."""
    _ensure_repo_root_on_path()
    try:
        import om5_core  # type: ignore

        return om5_core
    except Exception:
        root = _ensure_repo_root_on_path()
        path = root / "om5_core.py"
        if not path.is_file():
            return None
        spec = importlib.util.spec_from_file_location("om5_core", path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules["om5_core"] = mod
        return mod


def default_evolution_model() -> str:
    raw = (
        os.getenv("OM_EVOLUTION_DEFAULT")
        or os.getenv("OM_DEFAULT_MODEL")
        or "OM-L5"
    ).strip()
    return resolve_model_id(raw)


def resolve_model_id(model: str | None) -> str:
    if not model:
        return default_evolution_model()
    key = str(model).strip()
    low = key.lower()
    if key in {m["id"] for m in EVOLUTION_MODELS}:
        return key
    if low in _ALIASES:
        return _ALIASES[low]
    m = re.search(r"(?:level[\s_-]*)?([1-5])(?:\.0)?$", low)
    if not m:
        m = re.search(r"\bl\s*([1-5])\b", low)
    if m:
        return f"OM-L{m.group(1)}"
    return key


def level_for_model(model: str | None) -> float | None:
    mid = resolve_model_id(model)
    for row in EVOLUTION_MODELS:
        if row["id"] == mid:
            return float(row["level"])
    if mid == "OM-1.0":
        return 1.0
    return None


def catalog_models(*, settings: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    settings = settings or {}
    out: list[dict[str, Any]] = []
    for row in EVOLUTION_MODELS:
        item = dict(row)
        item["temperature"] = settings.get("temperature", row["temperature"])
        out.append(item)
    out.append(
        {
            "id": "OM-1.0",
            "name": "OM-1.0 Native (alias → Level 1)",
            "kind": "native",
            "level": 1.0,
            "description": "Legacy id; routes to Level 1 live native chat.",
            "temperature": settings.get("temperature", 0.7),
            "context_length": 256,
            "max_tokens": 256,
        }
    )
    return out


def _latest_user(messages: list[dict]) -> str:
    for m in reversed(messages or []):
        if str(m.get("role") or "") == "user":
            return str(m.get("content") or "").strip()
    return ""


def wants_matrix_mode(prompt: str, level: float) -> bool:
    """Matrix/sandbox only for agentic or numeric goals — not for 'hi' / 'what is AI'."""
    text = (prompt or "").strip()
    if not text:
        return False
    if _CHATTY.match(text):
        return False
    if level <= 1.0:
        return False
    if abs(level - 2.0) < 0.01:
        # Reasoner: matrix-style scratchpad for longer / analytical asks only
        return len(text) > 40 or bool(
            re.search(r"\b(why|how|analyze|explain|compare|reason|step[- ]by[- ]step)\b", text, re.I)
        )
    if abs(level - 3.0) < 0.01:
        return bool(_MATRIX_HINT.search(text)) or bool(re.search(r"[\d\s]*[\+\-\*/][\d\s]+", text))
    if abs(level - 4.0) < 0.01:
        return bool(re.search(r"\b(invent|novel|hypothesis|discover|innovate|research)\b", text, re.I))
    # L5
    return bool(_MATRIX_HINT.search(text)) or bool(
        re.search(r"\b(plan|strategy|roadmap|coordinate|launch|deploy)\b", text, re.I)
    )


def _plain_paragraphs(*parts: str) -> str:
    """Join non-empty parts with blank lines; no titles or labels."""
    chunks = [re.sub(r"[ \t]+\n", "\n", p.strip()) for p in parts if (p or "").strip()]
    return "\n\n".join(chunks).strip() + "\n"


def process_evolution_level(user_prompt: str, level: float) -> str:
    """Agentic replies as plain English only (no [OM-Lx] banners or section titles)."""
    if level <= 1.0:
        return ""
    if abs(level - 2.0) < 0.01:
        return _plain_paragraphs(
            "I will clarify the question, separate facts from assumptions, "
            "and answer in plain language.",
            f"Your question: {user_prompt}",
        )
    if abs(level - 3.0) < 0.01:
        om5 = _load_om5()
        m = re.search(r"(\d+\s*[\*\+\-/]\s*\d+)", user_prompt)
        nums = [int(n) for n in re.findall(r"\d+", user_prompt)]
        if m:
            code = f"print({m.group(1).replace(' ', '')})"
        elif nums:
            code = f"print({nums[0]} * 50)"
        else:
            code = "print(10 * 50)"
        if om5 is not None:
            out = str(om5.OMSandbox.execute_python(code)).strip()
        else:
            out = "The sandbox is unavailable right now."
        return _plain_paragraphs(
            f"I ran this calculation for you:\n{code}",
            f"Result: {out}",
        )
    if abs(level - 4.0) < 0.01:
        return _plain_paragraphs(
            f"Working idea based on your request: {user_prompt}",
            "This is an early research stub. Stronger results need more training data "
            "and evaluation, not just a prompt template.",
        )
    # L5 — plain summary; JSON/details stay internal when useful
    today = dt.datetime.now().strftime("%A, %B %d, %Y")
    om5 = _load_om5()
    sandbox = ""
    code = ""
    task_lines: list[str] = []
    if om5 is not None:
        try:
            plan = om5.json_multi_agent_dispatch(user_prompt)
            code = om5._budget_script(user_prompt)
            sandbox = str(om5.OMSandbox.execute_python(code)).strip()
            for t in plan.tasks:
                t.status = "done"
                t.result = sandbox if "finance" in t.agent else "ok"
                label = str(getattr(t, "agent", "") or "step").replace("_", " ")
                task_lines.append(f"- {label}: {t.result}")
        except Exception as exc:
            sandbox = f"Could not finish the sandbox step ({exc})."
    else:
        sandbox = "The organization helper module is not loaded."

    parts = [
        f"Goal: {user_prompt}",
        f"Date: {today}",
    ]
    if task_lines:
        parts.append("Steps taken:\n" + "\n".join(task_lines))
    if code and code != "n/a":
        parts.append(f"Code used:\n{code}")
    if sandbox:
        parts.append(f"Result: {sandbox}")
    parts.append(
        "This is a planning helper on top of OM-1.0 chat, not full organization AGI."
    )
    return _plain_paragraphs(*parts)


def maybe_evolution_reply(
    messages: list[dict],
    *,
    model: str | None,
) -> tuple[str | None, str, float | None]:
    """Return (reply_or_None, resolved_model_id, level). None → native OM chat."""
    mid = resolve_model_id(model)
    level = level_for_model(mid)
    if level is None:
        return None, mid, None
    user = _latest_user(messages)
    if not user:
        return "How can I help you today?", mid, level
    if level <= 1.0:
        return None, mid, level
    # Normal conversation on L2–L5 uses native OM-1.0 (not the matrix dump).
    if not wants_matrix_mode(user, level):
        return None, mid, level
    return process_evolution_level(user, level), mid, level
