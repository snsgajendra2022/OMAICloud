"""Companion web research — search & explain without opening a browser.

Default: fetch findings and speak naturally (brother-like care).
Only open Google/browser when the user explicitly says go / open / kholo.
Also stores concise notes so OM's local knowledge grows over time.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

_OPEN_INTENT = re.compile(
    r"(?i)\b("
    r"go|open|kholo|khol|launch|navigate|redirect|take\s+me|"
    r"browser\s+(me\s+)?kholo|open\s+(it|google|browser|the\s+link)|"
    r"google\s+(me\s+)?kholo|open\s+in\s+browser|show\s+in\s+browser"
    r")\b"
)

_SEARCH_INTENT = re.compile(
    r"(?i)\b(google|search|khoj|dhundo|find|look\s+up|research)\b|search\s+karo"
)


def wants_browser_open(text: str) -> bool:
    """True only when the user clearly asks to open/go to the browser."""
    return bool(_OPEN_INTENT.search(text or ""))


def is_search_request(text: str) -> bool:
    return bool(_SEARCH_INTENT.search(text or ""))


def extract_search_query(text: str) -> str:
    low = (text or "").strip()
    mq = re.search(
        r"(?i)(?:google(?:\s+search)?|search(?:\s+for)?|khoj|dhundo|look\s+up|find|research)\s+(.+)$",
        low,
    )
    q = (mq.group(1).strip(" .") if mq else "").strip()
    for junk in (
        "kholo",
        "khol",
        "open",
        "please",
        "karo",
        "on google",
        "pe",
        "par",
        "go",
        "launch",
        "navigate",
        "browser",
        "for me",
        "mere liye",
    ):
        q = re.sub(rf"(?i)\b{re.escape(junk)}\b", "", q).strip()
    q = re.sub(r"\s{2,}", " ", q).strip(" .,")
    if q.lower().startswith("search "):
        q = q[7:].strip()
    return q


def google_url(query: str) -> str:
    q = (query or "").strip()
    if not q:
        return "https://www.google.com"
    return f"https://www.google.com/search?q={quote_plus(q)}"


def _locale_hi(text: str) -> bool:
    low = (text or "").lower()
    return bool(
        re.search(
            r"[\u0900-\u097F]|\b(hai|hain|kya|tum|nahi|karo|batao|mujhe|bhai|theek)\b",
            low,
        )
    )


def research_query(query: str, *, user_message: str = "") -> dict[str, Any]:
    """Search the web (HTTP only) and return a natural spoken briefing."""
    q = (query or "").strip()
    hi = _locale_hi(user_message or q)
    if not q:
        msg = (
            "Bhai, kya search karna hai — topic bol do."
            if hi
            else "Tell me what to search, brother — give me the topic."
        )
        return {"ok": False, "query": "", "spoken": msg, "hits": [], "opened": False}

    hits: list[dict[str, str]] = []
    try:
        from om_ai.live_knowledge.web_search import search_web

        for r in search_web(q, limit=5) or []:
            hits.append(
                {
                    "title": str(getattr(r, "title", "") or ""),
                    "url": str(getattr(r, "url", "") or ""),
                    "snippet": str(getattr(r, "snippet", "") or ""),
                    "source": str(getattr(r, "source", "") or ""),
                }
            )
    except Exception:
        hits = []

    if not hits:
        try:
            from om_ai.live_knowledge.engine import LiveKnowledgeEngine

            pack = LiveKnowledgeEngine().collect(
                [{"role": "user", "content": q}],
                force=True,
            )
            grounded = str(getattr(pack, "grounded_reply", "") or "").strip()
            for ev in list(getattr(pack, "evidence", None) or [])[:5]:
                hits.append(
                    {
                        "title": str(getattr(ev, "title", "") or ""),
                        "url": str(getattr(ev, "url", "") or ""),
                        "snippet": str(getattr(ev, "text", "") or "")[:500],
                        "source": str(getattr(ev, "source", "") or "live"),
                    }
                )
            if grounded and not hits:
                hits.append({"title": q, "url": "", "snippet": grounded, "source": "live"})
        except Exception:
            pass

    spoken = _compose_briefing(q, hits, hi=hi)
    remember_search(q, hits, spoken=spoken)
    return {
        "ok": bool(hits),
        "query": q,
        "spoken": spoken,
        "hits": hits,
        "opened": False,
        "url": google_url(q),
    }


def _compose_briefing(query: str, hits: list[dict[str, str]], *, hi: bool) -> str:
    if not hits:
        if hi:
            return (
                f"Bhai, '{query}' pe abhi clear result nahi mila. "
                "Thoda specific bolo — main phir se dhoondhta hun. "
                "Browser kholne ke liye bolo 'go' ya 'open'."
            )
        return (
            f"Brother, I couldn't land a clear hit on “{query}” yet. "
            "Give me a sharper topic and I’ll dig again. "
            "Say “go” or “open” only if you want me to open Google."
        )

    top = hits[0]
    title = (top.get("title") or "").strip()
    snip = re.sub(r"\s+", " ", (top.get("snippet") or "").strip())
    if len(snip) > 280:
        snip = snip[:277].rsplit(" ", 1)[0] + "…"

    extras = []
    for h in hits[1:3]:
        t = (h.get("title") or "").strip()
        if t and t.lower() != title.lower():
            extras.append(t[:80])

    need = _solution_hint(query, snip, hi=hi)

    if hi:
        parts = [f"Bhai, maine '{query}' search kiya — bina browser khole."]
        if snip:
            parts.append(f"Mila yeh: {snip}")
        elif title:
            parts.append(f"Top hit: {title}.")
        if extras:
            parts.append("Related: " + "; ".join(extras) + ".")
        parts.append(need)
        parts.append("Browser kholna ho to bolo 'go' ya 'open'.")
        return " ".join(parts)

    parts = [f"Brother, I searched “{query}” for you — without opening the browser."]
    if snip:
        parts.append(f"Here’s what stood out: {snip}")
    elif title:
        parts.append(f"Top hit: {title}.")
    if extras:
        parts.append("Also related: " + "; ".join(extras) + ".")
    parts.append(need)
    parts.append("Say “go” or “open” only if you want me to open Google.")
    return " ".join(parts)


def _solution_hint(query: str, snippet: str, *, hi: bool) -> str:
    low = f"{query} {snippet}".lower()
    if any(w in low for w in ("error", "fix", "bug", "crash", "not working")):
        return (
            "Lagta hai problem/fix side pe focus chahiye — exact error line bhej do, main seedha solution nikaalta hun."
            if hi
            else "Looks like a fix is needed — send the exact error line and I’ll give you a direct solution."
        )
    if any(w in low for w in ("how to", "kaise", "steps", "guide", "tutorial")):
        return (
            "Next: main isko clear steps me tod ke bata sakta hun — bolo kahan tak pahunchna hai."
            if hi
            else "Next I can break this into clear steps — tell me how far you want to go."
        )
    if any(w in low for w in ("vs", "versus", "compare", "better", "choose")):
        return (
            "Choice chahiye to apna constraint bolo (budget, time, skill) — main seedha recommend karunga."
            if hi
            else "If you need a pick, tell me your constraint (budget, time, skill) and I’ll recommend clearly."
        )
    return (
        "Jo solution chahiye wo bolo — main us hisaab se aage badhta hun."
        if hi
        else "Tell me what outcome you want next and I’ll push toward that."
    )


def remember_search(query: str, hits: list[dict[str, str]], *, spoken: str = "") -> None:
    """Append search learning notes so local knowledge grows (honest incremental store)."""
    try:
        root = Path("artifacts") / "companion" / "knowledge_growth"
        root.mkdir(parents=True, exist_ok=True)
        path = root / "search_learnings.jsonl"
        note = {
            "ts": time.time(),
            "query": query,
            "hits": [
                {
                    "title": h.get("title", "")[:160],
                    "snippet": h.get("snippet", "")[:400],
                    "url": h.get("url", "")[:300],
                    "source": h.get("source", ""),
                }
                for h in (hits or [])[:5]
            ],
            "spoken_preview": (spoken or "")[:400],
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(note, ensure_ascii=False) + "\n")
    except Exception:
        pass
    try:
        from om_ai.core.companion_memory import get_memory_service

        mem = get_memory_service()
        blob = (hits[0].get("snippet") if hits else "") or query
        if hasattr(mem, "remember_fact"):
            mem.remember_fact(f"search:{query[:80]}", str(blob)[:500])
        elif hasattr(mem, "remember"):
            mem.remember("knowledge", f"{query}: {str(blob)[:400]}")
    except Exception:
        pass


def recall_search_context(query: str, *, limit: int = 3) -> str:
    """Pull recent related search notes into a short context blob."""
    path = Path("artifacts") / "companion" / "knowledge_growth" / "search_learnings.jsonl"
    if not path.is_file():
        return ""
    qlow = (query or "").lower()
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-200:]
        for line in reversed(lines):
            try:
                row = json.loads(line)
            except Exception:
                continue
            rq = str(row.get("query") or "").lower()
            if not rq:
                continue
            if qlow and (qlow in rq or rq in qlow or any(w in rq for w in qlow.split()[:4] if len(w) > 3)):
                rows.append(row)
            if len(rows) >= limit:
                break
    except Exception:
        return ""
    if not rows:
        return ""
    parts = ["[OM remembered search notes]"]
    for row in rows:
        parts.append(f"- {row.get('query')}: {str((row.get('hits') or [{}])[0].get('snippet') or '')[:180]}")
    return "\n".join(parts)
