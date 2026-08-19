"""Public web search helpers — HTTP retrieval only, never an LLM API."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

import httpx

from om_ai.live_knowledge.html_text import html_to_text

_UA = "OM-AI-LiveKnowledge/1.0 (+https://github.com/om-ai; retrieval-only)"


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str


def _client(timeout: float) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": _UA, "Accept": "application/json,text/html,*/*"},
    )


def duckduckgo_instant(query: str, *, timeout: float = 8.0) -> list[SearchResult]:
    """DuckDuckGo Instant Answer API (no key)."""
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    }
    out: list[SearchResult] = []
    try:
        with _client(timeout) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data: dict[str, Any] = r.json()
    except Exception:
        return out

    abstract = (data.get("AbstractText") or "").strip()
    abstract_url = (data.get("AbstractURL") or data.get("AbstractSource") or "").strip()
    heading = (data.get("Heading") or "").strip()
    if abstract:
        out.append(
            SearchResult(
                title=heading or "DuckDuckGo Abstract",
                url=abstract_url or "https://duckduckgo.com/",
                snippet=abstract[:800],
                source="duckduckgo_instant",
            )
        )

    for topic in data.get("RelatedTopics") or []:
        if not isinstance(topic, dict):
            continue
        if "Topics" in topic:
            continue
        text = (topic.get("Text") or "").strip()
        first = topic.get("FirstURL") or ""
        if text and first:
            out.append(
                SearchResult(
                    title=text.split(" - ")[0][:120],
                    url=first,
                    snippet=text[:500],
                    source="duckduckgo_related",
                )
            )
        if len(out) >= 5:
            break
    return out


def duckduckgo_html(query: str, *, timeout: float = 10.0, limit: int = 5) -> list[SearchResult]:
    """Parse DuckDuckGo HTML results page (fallback when Instant Answer is empty)."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    out: list[SearchResult] = []
    try:
        with _client(timeout) as client:
            r = client.get(url)
            r.raise_for_status()
            html = r.text
    except Exception:
        return out

    # Result blocks: <a class="result__a" href="...">title</a> + snippet
    for m in re.finditer(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div)',
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        href, title_html, snip_html = m.group(1), m.group(2), m.group(3)
        title = html_to_text(title_html, max_chars=200)
        snippet = html_to_text(snip_html, max_chars=400)
        # DDG sometimes wraps redirects
        if "uddg=" in href:
            from urllib.parse import parse_qs, urlparse

            qs = parse_qs(urlparse(href).query)
            href = (qs.get("uddg") or [href])[0]
        if not title or not href.startswith("http"):
            continue
        out.append(
            SearchResult(
                title=title,
                url=href,
                snippet=snippet,
                source="duckduckgo_html",
            )
        )
        if len(out) >= limit:
            break
    return out


def wikipedia_summary(query: str, *, timeout: float = 8.0) -> SearchResult | None:
    """MediaWiki REST summary for the best matching page."""
    try:
        with _client(timeout) as client:
            search = client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": query,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                },
            )
            search.raise_for_status()
            payload = search.json()
            titles = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            if not titles:
                return None
            title = titles[0]
            # REST endpoints expect underscores, not +encoded spaces
            slug = title.replace(" ", "_")
            summary = client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(slug, safe='_')}"
            )
            summary.raise_for_status()
            data = summary.json()
            extract = (data.get("extract") or "").strip()
            page_url = (
                (data.get("content_urls") or {}).get("desktop", {}) or {}
            ).get("page") or f"https://en.wikipedia.org/wiki/{slug}"
            if not extract:
                return None
            return SearchResult(
                title=data.get("title") or title,
                url=page_url,
                snippet=extract[:1200],
                source="wikipedia",
            )
    except Exception:
        return None


def wikipedia_summary_from_url(url: str, *, timeout: float = 8.0) -> SearchResult | None:
    """If ``url`` is a Wikipedia article, return the REST summary instead of scraping HTML."""
    from urllib.parse import unquote, urlparse

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if "wikipedia.org" not in host:
        return None
    parts = [p for p in (parsed.path or "").split("/") if p]
    if len(parts) < 2 or parts[0] != "wiki":
        return None
    slug = unquote(parts[1])
    try:
        with _client(timeout) as client:
            summary = client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(slug, safe='_')}"
            )
            summary.raise_for_status()
            data = summary.json()
            extract = (data.get("extract") or "").strip()
            if not extract:
                return None
            page_url = (
                (data.get("content_urls") or {}).get("desktop", {}) or {}
            ).get("page") or url
            return SearchResult(
                title=data.get("title") or slug.replace("_", " "),
                url=page_url,
                snippet=extract[:1200],
                source="wikipedia",
            )
    except Exception:
        return None


def search_web(query: str, *, timeout: float = 8.0, limit: int = 5) -> list[SearchResult]:
    """Aggregate Instant Answer → Wikipedia → HTML search."""
    seen: set[str] = set()
    merged: list[SearchResult] = []

    def _add(items: list[SearchResult]) -> None:
        for item in items:
            key = item.url.rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)

    _add(duckduckgo_instant(query, timeout=timeout))
    wiki = wikipedia_summary(query, timeout=timeout)
    if wiki:
        _add([wiki])
    if len(merged) < 2:
        _add(duckduckgo_html(query, timeout=timeout, limit=limit))
    return merged[:limit]
