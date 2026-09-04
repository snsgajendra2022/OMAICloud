"""
STEP 87 — OM Internet Intelligence Layer

Controlled internet understanding:
  Web Search → Retrieval → Website Understanding → Extraction → Verify
  with Identity + Permission + Sandbox + Rate Limit + Audit
"""
from __future__ import annotations

import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from om_ai.tools.intelligence.audit import ActionAuditLog


@dataclass
class InternetResult:
    ok: bool
    query: str
    snippets: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    verified: bool = False
    text: str = ""
    blocked_reason: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Simple sliding-window rate limit (default 20 req / 60s)."""

    def __init__(self, max_calls: int = 20, window_s: float = 60.0) -> None:
        self.max_calls = max_calls
        self.window_s = window_s
        self._hits: deque[float] = deque()

    def allow(self) -> bool:
        now = time.time()
        while self._hits and now - self._hits[0] > self.window_s:
            self._hits.popleft()
        if len(self._hits) >= self.max_calls:
            return False
        self._hits.append(now)
        return True


class InternetIntelligence:
    """Sandbox-aware web research — off unless OM_LIVE_KNOWLEDGE is enabled."""

    def __init__(self, *, identity: str = "default") -> None:
        self.identity = identity
        self.audit = ActionAuditLog(
            path=os.environ.get(
                "OM_INTERNET_AUDIT_LOG",
                "data/om-memory/internet_audit.jsonl",
            )
        )
        max_calls = int(os.environ.get("OM_INTERNET_RATE_LIMIT", "20") or "20")
        self.limiter = RateLimiter(max_calls=max_calls)

    def enabled(self) -> bool:
        return os.environ.get("OM_LIVE_KNOWLEDGE", "0").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }

    def network_enabled(self) -> bool:
        return os.environ.get("OM_LIVE_KNOWLEDGE_NETWORK", "0").strip() == "1"

    def research(self, query: str, *, k: int = 5) -> InternetResult:
        q = (query or "").strip()
        if not q:
            return InternetResult(ok=False, query=q, blocked_reason="empty_query")

        if not self.enabled():
            self.audit.record(
                {
                    "event": "blocked",
                    "actor": self.identity,
                    "reason": "live_off",
                    "q": q[:120],
                }
            )
            return InternetResult(
                ok=False,
                query=q,
                blocked_reason="OM_LIVE_KNOWLEDGE=0",
            )

        if not self.limiter.allow():
            self.audit.record(
                {"event": "rate_limited", "actor": self.identity, "q": q[:120]}
            )
            return InternetResult(ok=False, query=q, blocked_reason="rate_limited")

        snippets: list[str] = []
        sources: list[dict[str, Any]] = []

        try:
            from om_ai.agent.tools import maybe_live_grounding

            grounded = maybe_live_grounding(q, [])
            if grounded:
                snippets.append(str(grounded)[:3000])
                sources.append({"type": "live_grounding", "trusted": True})
        except Exception:
            pass

        if self.network_enabled() and len(snippets) < k:
            try:
                from om_ai.live_knowledge.web_search import search_web

                hits = search_web(q, limit=k) or []
                for h in hits:
                    if hasattr(h, "title"):
                        title = getattr(h, "title", "")
                        url = getattr(h, "url", "")
                        snippet = getattr(h, "snippet", "") or getattr(h, "text", "")
                        sources.append(
                            {
                                "title": title,
                                "url": url,
                                "type": "web",
                                "trusted": self._verify_source(url),
                            }
                        )
                        if snippet:
                            snippets.append(f"{title}: {snippet}"[:500])
                    elif isinstance(h, dict):
                        sources.append(
                            {
                                "title": h.get("title"),
                                "url": h.get("url"),
                                "type": "web",
                                "trusted": self._verify_source(str(h.get("url") or "")),
                            }
                        )
                        sn = str(h.get("snippet") or h.get("text") or "")
                        if sn:
                            snippets.append(sn[:500])
            except Exception as exc:
                sources.append({"type": "error", "detail": str(exc)})

        verified = any(s.get("trusted") for s in sources) if sources else bool(snippets)
        text = "\n\n".join(snippets[:k])
        ok = bool(text)
        self.audit.record(
            {
                "event": "research",
                "actor": self.identity,
                "q": q[:160],
                "ok": ok,
                "sources": len(sources),
                "verified": verified,
            }
        )
        return InternetResult(
            ok=ok,
            query=q,
            snippets=snippets[:k],
            sources=sources[:k],
            verified=verified,
            text=text,
            meta={"network": self.network_enabled()},
        )

    def _verify_source(self, url: str) -> bool:
        u = (url or "").lower()
        trusted_hosts = (
            "wikipedia.org",
            "gov",
            "edu",
            "docs.python.org",
            "developer.mozilla.org",
            "arxiv.org",
            "github.com",
        )
        return any(h in u for h in trusted_hosts) and u.startswith("https://")
