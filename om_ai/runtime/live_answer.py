"""Live web + Wikipedia grounded answers for chat (no external LLM)."""
from __future__ import annotations

import os
import re
from typing import Any


def live_enabled() -> bool:
    return os.environ.get("OM_LIVE_KNOWLEDGE", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def network_enabled() -> bool:
    # Default ON so chat can use Wikipedia/web for current knowledge.
    return os.environ.get("OM_LIVE_KNOWLEDGE_NETWORK", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


_NEEDS_LIVE = re.compile(
    r"\b("
    r"what\s+is|what\s+are|who\s+is|who\s+was|latest|current|today|recent|"
    r"version|release|news|price|how\s+to|install|create|build|"
    r"react|python|javascript|typescript|node|next\.?js|vue|angular|"
    r"django|fastapi|docker|kubernetes|aws|wiki|wikipedia|"
    r"explain|define|documentation|docs|language|framework|library"
    r")\b",
    re.I,
)

_TECH_WIKI = {
    "react": "React (software)",
    "python": "Python (programming language)",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vue": "Vue.js",
    "angular": "Angular (web framework)",
    "django": "Django (web framework)",
    "fastapi": "FastAPI",
    "docker": "Docker (software)",
    "kubernetes": "Kubernetes",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "redis": "Redis",
}


def needs_live_knowledge(question: str) -> bool:
    q = (question or "").strip()
    if not q or len(q) < 3:
        return False
    try:
        from om_ai.live_knowledge.freshness import is_greeting_like, is_chitchat

        if is_greeting_like(q) or is_chitchat(q):
            return False
    except Exception:
        pass
    letters = re.findall(r"[a-zA-Z]", q)
    if len(q.split()) <= 2 and letters:
        vowels = sum(1 for c in letters if c.lower() in "aeiou")
        if vowels / max(len(letters), 1) < 0.2:
            return False
    return bool(_NEEDS_LIVE.search(q)) or len(q.split()) >= 4


def _wiki_topic(question: str) -> str:
    q = (question or "").strip()
    low = q.lower()
    for key, title in _TECH_WIKI.items():
        if re.search(rf"\b{re.escape(key)}\b", low):
            return title
    m = re.search(r"\bwhat\s+is\s+(.+)$", q, re.I)
    if m:
        return m.group(1).strip(" ?.")
    return q


def _is_weak_snippet(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t or len(t) < 40:
        return True
    if "may refer to" in t or "can refer to" in t:
        return True
    if t.startswith("sources:"):
        return True
    return False


def _prefer_hit(hits: list[dict[str, str]], question: str) -> dict[str, str] | None:
    qlow = (question or "").lower()
    scored: list[tuple[int, dict[str, str]]] = []
    for h in hits:
        sn = h.get("snippet") or ""
        if _is_weak_snippet(sn):
            continue
        score = 0
        src = (h.get("source") or "").lower()
        url = (h.get("url") or "").lower()
        title = (h.get("title") or "").lower()
        if src == "wikipedia" or "wikipedia.org" in url:
            score += 5
            if "programming language" in title or "(software)" in title:
                score += 4
        if any(d in url for d in ("react.dev", "npmjs.com", "python.org", "developer.mozilla.org", "docs.")):
            score += 6
        if re.search(r"\b(latest|version|release)\b", qlow):
            if re.search(r"\d+\.\d+", sn):
                score += 3
            if "npmjs.com" in url or "versions" in url:
                score += 4
        scored.append((score, h))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def fetch_live_pack(question: str, *, limit: int = 5) -> dict[str, Any]:
    """Retrieve Wikipedia + web snippets for a question."""
    q = (question or "").strip()
    out: dict[str, Any] = {
        "ok": False,
        "query": q,
        "hits": [],
        "wikipedia": None,
        "context": "",
        "answer": "",
        "sources": [],
    }
    if not q or not live_enabled() or not network_enabled():
        out["reason"] = "live_or_network_off"
        return out

    hits: list[dict[str, str]] = []
    try:
        from om_ai.live_knowledge.web_search import search_web, wikipedia_summary

        wiki = wikipedia_summary(_wiki_topic(q))
        if wiki and getattr(wiki, "snippet", None) and not _is_weak_snippet(wiki.snippet):
            out["wikipedia"] = {
                "title": wiki.title,
                "url": wiki.url,
                "snippet": wiki.snippet,
            }
            hits.append(
                {
                    "title": wiki.title,
                    "url": wiki.url,
                    "snippet": wiki.snippet,
                    "source": "wikipedia",
                }
            )

        for h in search_web(q, limit=limit) or []:
            snip = str(getattr(h, "snippet", "") or "")
            if _is_weak_snippet(snip):
                continue
            hits.append(
                {
                    "title": str(getattr(h, "title", "") or ""),
                    "url": str(getattr(h, "url", "") or ""),
                    "snippet": snip,
                    "source": str(getattr(h, "source", "") or "web"),
                }
            )
    except Exception as exc:
        out["error"] = str(exc)
        return out

    seen: set[str] = set()
    uniq: list[dict[str, str]] = []
    for h in hits:
        url = (h.get("url") or "").rstrip("/").lower()
        if not url or url in seen:
            continue
        seen.add(url)
        uniq.append(h)
    out["hits"] = uniq[:limit]
    out["sources"] = [
        {"title": h["title"], "url": h["url"], "source": h.get("source", "web")}
        for h in out["hits"]
    ]
    out["context"] = "\n\n".join(
        f"{h['title']}: {h['snippet'][:500]}" for h in out["hits"]
    )[:5000]
    out["answer"] = format_live_answer(q, out["hits"])
    out["ok"] = bool(out["answer"]) and not _is_weak_snippet(out["answer"])
    return out


def format_live_answer(question: str, hits: list[dict[str, str]]) -> str:
    if not hits:
        return ""
    qlow = (question or "").lower()
    primary = _prefer_hit(hits, question)
    if not primary:
        return ""

    body = (primary.get("snippet") or "").strip()
    title = (primary.get("title") or "").strip()
    if _is_weak_snippet(body):
        return ""

    version_note = ""
    if re.search(r"\b(latest|current|version|release|verion|lestest)\b", qlow):
        # Prefer npm / official docs for version numbers
        for h in sorted(
            hits,
            key=lambda x: (
                0
                if "npmjs.com" in (x.get("url") or "").lower()
                else 1
                if "react.dev" in (x.get("url") or "").lower()
                else 2
            ),
        ):
            sn = h.get("snippet") or ""
            m = re.search(
                r"(?:latest\s+version\s*:?\s*|version\s*)(\d+(?:\.\d+){1,3})",
                sn,
                re.I,
            )
            if m:
                version_note = f"Latest version found online: **{m.group(1)}**.\n\n"
                break
            m2 = re.search(r"\b(?:React|Python|Node\.?js)\s+v?(\d+(?:\.\d+){0,2})\b", sn, re.I)
            if m2:
                version_note = f"Current version referenced online: **{m2.group(0)}**.\n\n"
                break

    parts: list[str] = []
    if version_note:
        parts.append(version_note.strip())
    if title and title.lower() not in body.lower()[:100]:
        parts.append(f"**{title}**\n\n{body}")
    else:
        parts.append(body)

    parts.append("")
    parts.append("Sources:")
    for h in hits[:5]:
        t = h.get("title") or "Source"
        u = h.get("url") or ""
        if u:
            parts.append(f"- {t}: {u}")
    return "\n".join(parts).strip()


def live_or_fallback(question: str, fallback: str = "") -> str:
    """Prefer live web/Wikipedia answer; else fallback text."""
    if needs_live_knowledge(question):
        pack = fetch_live_pack(question)
        if pack.get("ok") and pack.get("answer"):
            return str(pack["answer"])
    return (fallback or "").strip()
