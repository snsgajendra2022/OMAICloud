"""HTTP fetch for live knowledge (deterministic retrieval, not an LLM)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from om_ai.live_knowledge.html_text import extract_title, html_to_text

_UA = "OM-AI-LiveKnowledge/1.0 (+retrieval-only; no-llm)"


@dataclass(frozen=True)
class FetchResult:
    url: str
    ok: bool
    status_code: int | None = None
    title: str = ""
    text: str = ""
    error: str | None = None
    stub: bool = False


def fetch_url(
    url: str,
    *,
    timeout: float = 8.0,
    max_chars: int = 4000,
    allow_network: bool = False,
) -> FetchResult:
    """Fetch a URL when ``allow_network`` is True; otherwise return an honest stub.

    Never calls OpenAI/Ollama or any LLM API.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return FetchResult(url=url, ok=False, error="invalid URL", stub=True)

    if not allow_network:
        return FetchResult(
            url=url,
            ok=False,
            title="(fetch stub)",
            text=(
                f"[OM live_knowledge stub] Network fetch disabled for {url}. "
                "Enable OM_LIVE_KNOWLEDGE_NETWORK=1 for real HTTP retrieval. "
                "Synthesis must still use OM-1.0 only."
            ),
            error="network_disabled",
            stub=True,
        )

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": _UA},
        ) as client:
            r = client.get(url)
            raw = r.text or ""
            ctype = (r.headers.get("content-type") or "").lower()
            if "html" in ctype or raw.lstrip().lower().startswith("<!doctype") or "<html" in raw[:200].lower():
                title = extract_title(raw)
                text = html_to_text(raw, max_chars=max_chars)
            else:
                title = ""
                text = raw[:max_chars]
            return FetchResult(
                url=str(r.url),
                ok=r.status_code < 400,
                status_code=r.status_code,
                title=title,
                text=text,
            )
    except Exception as exc:
        return FetchResult(url=url, ok=False, error=str(exc))


def fetch_many(urls: list[str], **kwargs: Any) -> list[FetchResult]:
    return [fetch_url(u, **kwargs) for u in urls]
