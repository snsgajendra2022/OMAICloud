"""OM Live Knowledge engine — retrieve + ground facts; never call another LLM."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from om_ai.live_knowledge.fetcher import FetchResult, fetch_url
from om_ai.live_knowledge.freshness import FreshnessRouter
from om_ai.live_knowledge.search import LocalSearchIndex, SearchHit, index_text_files
from om_ai.live_knowledge.sources import local_roots, urls_for_query
from om_ai.live_knowledge.web_search import SearchResult, search_web, wikipedia_summary_from_url


def network_enabled() -> bool:
    """Real HTTP retrieval when OM_LIVE_KNOWLEDGE_NETWORK=1 (default off for offline tests)."""
    return (os.getenv("OM_LIVE_KNOWLEDGE_NETWORK") or "").strip() == "1"


def live_knowledge_enabled() -> bool:
    """Master switch; default on. Set OM_LIVE_KNOWLEDGE=0 to disable enrichment."""
    raw = (os.getenv("OM_LIVE_KNOWLEDGE") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


@dataclass
class Evidence:
    title: str
    url: str
    text: str
    source: str
    score: float = 0.0


@dataclass
class LiveKnowledgeResult:
    needs_live: bool
    reason: str
    query: str
    evidence: list[Evidence] = field(default_factory=list)
    grounded_reply: str | None = None
    context_block: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@lru_cache(maxsize=1)
def _default_local_index() -> LocalSearchIndex:
    idx = LocalSearchIndex()
    for root in local_roots():
        index_text_files(root, index=idx)
    return idx


def reset_local_index_cache() -> None:
    _default_local_index.cache_clear()


def _compact(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return (cut or text[:limit]).rstrip(".,;:") + "…"


def strip_live_knowledge_boilerplate(text: str) -> str:
    """Remove old dump headers and source URLs from user-facing replies."""
    s = (text or "").strip()
    if not s:
        return s
    s = re.sub(
        r"(?is)^Live knowledge\s*\(retrieved[^)]*\)\s*:?\s*",
        "",
        s,
    ).strip()
    s = re.sub(r"(?im)^Question:\s*.+$", "", s).strip()
    s = re.sub(
        r"(?is)\n*OM-1\.0 should treat the facts above[\s\S]*$",
        "",
        s,
    ).strip()
    # Drop bare URL lines and "Source: …" lines.
    s = re.sub(r"(?im)^\s*Source:\s*\S+\s*$", "", s)
    s = re.sub(r"(?im)^\s*https?://\S+\s*$", "", s)
    s = re.sub(r"\s*\(https?://[^)]+\)", "", s)
    s = re.sub(r"(?m)^\d+\.\s+.+\n", "", s)  # numbered titles
    if re.match(r"(?m)^\d+\.\s+", s):
        chunks: list[str] = []
        for m in re.finditer(
            r"(?ms)^\d+\.\s+(.+?)\n\s*(.+?)(?:\n\s*Source:\s*\S+)?(?:\n\n|\Z)",
            s,
        ):
            body = re.sub(r"\s+", " ", m.group(2).strip())
            if body:
                chunks.append(body)
        if chunks:
            return chunks[0]
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def compose_grounded_reply(query: str, evidence: list[Evidence]) -> str | None:
    """Direct natural answer — plain text only, no URLs / no numbered dump."""
    if not evidence:
        return None
    filtered: list[Evidence] = []
    for ev in evidence:
        blob = f"{ev.title} {ev.text} {ev.url}".lower()
        if any(x in blob for x in ("ollama", "chatgpt", "openai.com", "gpt-4", "claude")):
            continue
        filtered.append(ev)
    if not filtered:
        filtered = list(evidence)

    top = filtered[0]
    answer = _compact(top.text, 650)
    if not answer:
        return None
    return answer


def compose_context_block(evidence: list[Evidence], *, max_chars: int = 900) -> str:
    """Ultra-short system/user injection for OM-1.0's tight context window."""
    if not evidence:
        return ""
    parts = ["[OM live knowledge — retrieved facts, not an external LLM]"]
    budget = max_chars - len(parts[0])
    for ev in evidence[:3]:
        chunk = f"- {ev.title or ev.source}: {_compact(ev.text, 220)}"
        if ev.url:
            chunk += f" ({ev.url})"
        if len(chunk) + 1 > budget:
            break
        parts.append(chunk)
        budget -= len(chunk) + 1
    return "\n".join(parts)


class LiveKnowledgeEngine:
    """Freshness → local index → URL hints → web search → page fetch → grounded text."""

    def __init__(
        self,
        *,
        index: LocalSearchIndex | None = None,
        router: FreshnessRouter | None = None,
        allow_network: bool | None = None,
    ) -> None:
        self.router = router or FreshnessRouter()
        self.index = index if index is not None else _default_local_index()
        self.allow_network = network_enabled() if allow_network is None else allow_network

    def collect(self, messages: list[dict], *, force: bool = False) -> LiveKnowledgeResult:
        decision = self.router.decide(messages, force=force)
        result = LiveKnowledgeResult(
            needs_live=decision.needs_live,
            reason=decision.reason,
            query=decision.query,
            meta={
                "needs_live": decision.needs_live,
                "reason": decision.reason,
                "hits": [],
                "fetches": [],
                "web": [],
                "llm_used": None,
                "network": self.allow_network,
            },
        )
        if not decision.needs_live:
            return result

        evidence: list[Evidence] = []

        # 1) Local docs — only strong lexical matches (avoid random docs/ noise)
        local_hits: list[SearchHit] = self.index.search(decision.query, limit=5)
        min_local = 3.0 if self.allow_network else 1.2
        strong_local = [h for h in local_hits if h.score >= min_local]
        result.meta["hits"] = [
            {"doc_id": h.doc_id, "score": h.score, "snippet": h.snippet, "source": h.source}
            for h in strong_local
        ]
        for h in strong_local[:2]:
            evidence.append(
                Evidence(
                    title=h.doc_id,
                    url="",
                    text=h.snippet,
                    source=h.source,
                    score=h.score,
                )
            )

        # 2) Hint URLs + any URL in query (highest priority for known topics)
        hint_urls = urls_for_query(decision.query)
        for url in hint_urls[:3]:
            wiki = wikipedia_summary_from_url(url) if self.allow_network else None
            if wiki and wiki.snippet:
                result.meta["fetches"].append(
                    {
                        "url": wiki.url,
                        "ok": True,
                        "stub": False,
                        "error": None,
                        "title": wiki.title,
                    }
                )
                evidence.append(
                    Evidence(
                        title=wiki.title,
                        url=wiki.url,
                        text=wiki.snippet,
                        source="wikipedia",
                        score=5.5,
                    )
                )
                continue
            fr = fetch_url(url, allow_network=self.allow_network, max_chars=3500)
            result.meta["fetches"].append(
                {
                    "url": fr.url,
                    "ok": fr.ok,
                    "stub": fr.stub,
                    "error": fr.error,
                    "title": fr.title,
                }
            )
            if fr.ok and fr.text:
                # JSON REST bodies: pull extract if present
                text = fr.text
                if text.lstrip().startswith("{"):
                    try:
                        import json as _json

                        data = _json.loads(text)
                        if isinstance(data, dict) and data.get("extract"):
                            text = str(data["extract"])
                            title = str(data.get("title") or fr.title)
                        else:
                            title = fr.title
                    except Exception:
                        title = fr.title
                else:
                    title = fr.title
                evidence.append(
                    Evidence(
                        title=title or fr.url,
                        url=fr.url,
                        text=text,
                        source="fetch",
                        score=5.0,
                    )
                )

        # 3) Web search (DDG + Wikipedia) when network on
        if self.allow_network:
            try:
                web_hits = search_web(decision.query, limit=4)
            except Exception as exc:
                web_hits = []
                result.meta["web_error"] = str(exc)
            result.meta["web"] = [
                {"title": w.title, "url": w.url, "snippet": w.snippet, "source": w.source}
                for w in web_hits
            ]
            for w in web_hits:
                evidence.append(
                    Evidence(
                        title=w.title,
                        url=w.url,
                        text=w.snippet,
                        source=w.source,
                        score=4.0 if w.source == "wikipedia" else 3.5,
                    )
                )
                # Prefer Wikipedia REST over HTML scrape (HTML often 403s bots)
                if "wikipedia.org" in w.url:
                    wiki = wikipedia_summary_from_url(w.url)
                    if wiki and wiki.snippet:
                        evidence.append(
                            Evidence(
                                title=wiki.title,
                                url=wiki.url,
                                text=wiki.snippet,
                                source="wikipedia",
                                score=5.5,
                            )
                        )
                        result.meta["fetches"].append(
                            {
                                "url": wiki.url,
                                "ok": True,
                                "stub": False,
                                "error": None,
                                "title": wiki.title,
                            }
                        )
                        continue
                if w.source in {"wikipedia", "duckduckgo_instant"} and w.url.startswith("http"):
                    fr = fetch_url(w.url, allow_network=True, max_chars=2500)
                    result.meta["fetches"].append(
                        {
                            "url": fr.url,
                            "ok": fr.ok,
                            "stub": fr.stub,
                            "error": fr.error,
                            "title": fr.title,
                        }
                    )
                    if fr.ok and fr.text:
                        evidence.append(
                            Evidence(
                                title=fr.title or w.title,
                                url=fr.url,
                                text=fr.text,
                                source=f"{w.source}_page",
                                score=5.5 if w.source == "wikipedia" else 4.5,
                            )
                        )

        # Prefer higher-score / longer text; drop weak local when web/fetch exists
        evidence = _dedupe_evidence(evidence)
        if any(e.source != "local" and not e.source.startswith("local") for e in evidence):
            evidence = [
                e
                for e in evidence
                if e.source not in {"local"} and not str(e.source).startswith("local:")
            ] or evidence
        result.evidence = evidence
        result.context_block = compose_context_block(evidence)
        result.grounded_reply = compose_grounded_reply(decision.query, evidence)
        result.meta["evidence_count"] = len(evidence)
        result.meta["has_grounded_reply"] = bool(result.grounded_reply)
        if not evidence and not self.allow_network:
            result.context_block = (
                "[OM live knowledge] Time-sensitive query detected, but network "
                "retrieval is off (set OM_LIVE_KNOWLEDGE_NETWORK=1). "
                "Answer from OM-1.0 weights and note live data may be unavailable."
            )
            result.meta["fetches"].append(
                {
                    "url": "",
                    "ok": False,
                    "stub": True,
                    "error": "network_disabled",
                    "title": "",
                }
            )
        return result


def _dedupe_evidence(items: list[Evidence]) -> list[Evidence]:
    seen: set[str] = set()
    out: list[Evidence] = []
    for ev in sorted(items, key=lambda e: (e.score, len(e.text)), reverse=True):
        key = (ev.url or ev.title or ev.text[:80]).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
    return out[:6]


def inject_context(
    messages: list[dict],
    context_block: str,
) -> list[dict[str, str]]:
    """Attach compact retrieval context for OM-1.0 (prefer last user turn)."""
    out: list[dict[str, str]] = [
        {"role": str(m.get("role") or "user"), "content": str(m.get("content") or "")}
        for m in messages
    ]
    if not (context_block or "").strip():
        return out

    # Prefer injecting into the last user message so tiny max_seq_len models
    # keep the question + facts together after history trimming.
    for i in range(len(out) - 1, -1, -1):
        if out[i]["role"] == "user":
            out[i] = {
                "role": "user",
                "content": f"{context_block}\n\nUser question: {out[i]['content']}",
            }
            return out

    out.insert(0, {"role": "system", "content": context_block})
    return out
