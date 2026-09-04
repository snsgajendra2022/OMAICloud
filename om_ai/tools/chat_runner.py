"""Execute planned chat tools — not just list them.

Used by CognitiveIntelligence + AgentBrain so tools are not skipped.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def tools_enabled() -> bool:
    return os.environ.get("OM_CHAT_TOOLS", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _run_date() -> dict[str, Any]:
    try:
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        now = datetime.now().astimezone()
    text = f"Today's date is {now.strftime('%A, %d %B %Y')}."
    return {"tool": "date", "ok": True, "output": text, "text": text}


def _run_calculator(question: str) -> dict[str, Any]:
    q = question or ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", q, re.I)
    if m:
        pct, base = float(m.group(1)), float(m.group(2))
        text = f"{pct}% of {base:g} = {(pct / 100.0) * base:g}"
        return {"tool": "calculator", "ok": True, "output": text, "text": text}
    expr = re.search(r"([\d\.\s\+\-\*\/\(\)]+)", q)
    if expr:
        raw = expr.group(1).strip()
        if re.fullmatch(r"[\d\.\s\+\-\*\/\(\)]+", raw) and any(c.isdigit() for c in raw):
            try:
                val = eval(raw, {"__builtins__": {}}, {})  # noqa: S307
                if isinstance(val, (int, float)):
                    text = f"{raw.strip()} = {val:g}"
                    return {"tool": "calculator", "ok": True, "output": text, "text": text}
            except Exception:
                pass
    return {"tool": "calculator", "ok": False, "output": "no expression", "text": ""}


def _run_knowledge(question: str, *, tenant_id: str = "default") -> dict[str, Any]:
    snippets: list[str] = []
    try:
        from om_ai.agent.tools import search_knowledge

        snippets = search_knowledge(question, tenant_id=tenant_id, k=6) or []
    except Exception:
        pass
    if not snippets:
        try:
            from om_ai.brain.dataset_engine import retrieve_answer

            hit = retrieve_answer(question, min_score=0.35)
            if hit and hit.get("answer"):
                snippets = [str(hit["answer"])]
        except Exception:
            pass
    if not snippets:
        try:
            from om_ai.knowledge.facts import lookup_fact

            hit = lookup_fact(question)
            if hit and hit.get("answer"):
                snippets = [str(hit["answer"])]
        except Exception:
            pass
    text = "\n\n".join(s for s in snippets[:4] if s)
    return {
        "tool": "knowledge",
        "ok": bool(text),
        "output": snippets[:4],
        "text": text,
    }


def _run_file(question: str, *, root: str = ".") -> dict[str, Any]:
    root_path = Path(root).resolve()
    q = (question or "").lower()
    # Safe list / read of small workspace files mentioned in the ask
    candidates: list[Path] = []
    for pat in ("README.md", "readme.md", "pyproject.toml", "package.json", ".env.example"):
        p = root_path / pat
        if p.is_file():
            candidates.append(p)
    # Explicit path-like tokens
    for m in re.finditer(r"([\w./-]+\.(py|md|txt|json|toml|yml|yaml))", question or ""):
        p = (root_path / m.group(1)).resolve()
        try:
            p.relative_to(root_path)
        except ValueError:
            continue
        if p.is_file():
            candidates.append(p)
    texts: list[str] = []
    for p in candidates[:3]:
        try:
            body = p.read_text(encoding="utf-8", errors="replace")[:2500]
            texts.append(f"**File: {p.name}**\n```\n{body}\n```")
        except Exception:
            continue
    if not texts and ("list" in q or "files" in q or "folder" in q):
        try:
            names = sorted(
                x.name for x in root_path.iterdir() if not x.name.startswith(".")
            )[:30]
            texts.append("Workspace files: " + ", ".join(names))
        except Exception:
            pass
    text = "\n\n".join(texts)
    return {"tool": "file", "ok": bool(text), "output": texts, "text": text}


def _run_code(question: str, *, root: str = ".") -> dict[str, Any]:
    try:
        from om_ai.coding_brain import handle

        out = handle(question, root=root, dry_run=True)
        md = str(out.get("reasoning_markdown") or "").strip()
        plan = out.get("plan") or {}
        bits: list[str] = []
        if md:
            bits.append(md[:4000])
        if isinstance(plan, dict):
            summary = str(plan.get("summary") or plan.get("markdown") or "").strip()
            if summary:
                bits.append(summary[:2000])
        text = "\n\n".join(bits)
        return {
            "tool": "code_execution",
            "ok": bool(text),
            "output": {"plan": plan, "has_markdown": bool(md)},
            "text": text,
        }
    except Exception as exc:
        return {"tool": "code_execution", "ok": False, "output": str(exc), "text": ""}


def _run_web(question: str) -> dict[str, Any]:
    try:
        from om_ai.internet import InternetIntelligence

        result = InternetIntelligence().research(question, k=5)
        if result.ok and result.text:
            return {
                "tool": "web",
                "ok": True,
                "output": {
                    "sources": result.sources,
                    "verified": result.verified,
                },
                "text": result.text,
            }
        if result.blocked_reason:
            return {
                "tool": "web",
                "ok": False,
                "output": result.blocked_reason,
                "text": "",
            }
    except Exception:
        pass
    if os.environ.get("OM_LIVE_KNOWLEDGE", "0").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return {"tool": "web", "ok": False, "output": "live knowledge off", "text": ""}
    try:
        from om_ai.agent.tools import maybe_live_grounding

        grounded = maybe_live_grounding(question, [])
        if grounded:
            return {"tool": "web", "ok": True, "output": grounded, "text": grounded}
    except Exception as exc:
        return {"tool": "web", "ok": False, "output": str(exc), "text": ""}
    return {"tool": "web", "ok": False, "output": "no results", "text": ""}


def _run_vision(question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = context or {}
    path = str(ctx.get("image_path") or ctx.get("attachment") or "").strip()
    if not path:
        return {"tool": "vision", "ok": False, "output": "no image", "text": ""}
    try:
        from om_ai.operating_intelligence import perception_bridge

        fn = getattr(perception_bridge, "analyze_image", None)
        if callable(fn):
            result = fn(path, question=question)
            if isinstance(result, dict):
                text = str(result.get("summary") or result.get("answer") or "")
            else:
                text = str(result or "")
            return {"tool": "vision", "ok": bool(text), "output": result, "text": text}
    except Exception as exc:
        return {"tool": "vision", "ok": False, "output": str(exc), "text": ""}
    return {"tool": "vision", "ok": False, "output": "unavailable", "text": ""}


_HANDLERS = {
    "date": lambda q, ctx: _run_date(),
    "calculator": lambda q, ctx: _run_calculator(q),
    "knowledge": lambda q, ctx: _run_knowledge(q, tenant_id=str(ctx.get("tenant_id") or "default")),
    "file": lambda q, ctx: _run_file(q, root=str(ctx.get("project_root") or ctx.get("root") or ".")),
    "code_execution": lambda q, ctx: _run_code(q, root=str(ctx.get("project_root") or ctx.get("root") or ".")),
    "code": lambda q, ctx: _run_code(q, root=str(ctx.get("project_root") or ctx.get("root") or ".")),
    "web": lambda q, ctx: _run_web(q),
    "vision": lambda q, ctx: _run_vision(q, ctx),
    "ocr": lambda q, ctx: _run_vision(q, ctx),
}


def execute_planned_tools(
    tool_names: list[str] | None,
    question: str,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run each planned tool and return merged results for the answer stage."""
    if not tools_enabled():
        return {
            "enabled": False,
            "executed": [],
            "results": [],
            "texts": [],
            "combined_text": "",
            "skipped": True,
            "reason": "OM_CHAT_TOOLS=0",
        }

    ctx = dict(context or {})
    names = [str(n).strip() for n in (tool_names or []) if str(n).strip()]
    # Always try knowledge for substantive asks if nothing planned
    q = (question or "").strip()
    if not names and q and len(q.split()) >= 3:
        names = ["knowledge"]

    results: list[dict[str, Any]] = []
    texts: list[str] = []
    executed: list[str] = []

    for name in names:
        handler = _HANDLERS.get(name)
        if not handler:
            results.append({"tool": name, "ok": False, "output": "unknown tool", "text": ""})
            continue
        try:
            out = handler(q, ctx)
        except Exception as exc:
            out = {"tool": name, "ok": False, "output": str(exc), "text": ""}
        results.append(out)
        executed.append(name)
        t = str(out.get("text") or "").strip()
        if out.get("ok") and t:
            texts.append(t)

    combined = "\n\n".join(texts)
    return {
        "enabled": True,
        "executed": executed,
        "results": results,
        "texts": texts,
        "combined_text": combined,
        "skipped": False,
        "ok": bool(combined),
    }


def format_tool_context(tool_out: dict[str, Any]) -> str:
    """Short block to inject into capability / model context."""
    if not tool_out or tool_out.get("skipped"):
        return ""
    parts: list[str] = []
    for r in tool_out.get("results") or []:
        if not r.get("ok"):
            continue
        t = str(r.get("text") or "").strip()
        if not t:
            continue
        parts.append(f"[tool:{r.get('tool')}]\n{t[:2000]}")
    return "\n\n".join(parts)
