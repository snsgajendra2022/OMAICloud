"""Authorized single-host document fetch for live-knowledge ingestion.

This is not a general web spider. It fetches one approved URL (or a short
same-host link expansion) with SSRF protections. Mass scraping of third-party
sites is intentionally out of scope.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CrawlPage:
    url: str
    text: str
    status: int = 200
    stub: bool = False


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self._chunks.append(t)

    def text(self) -> str:
        return "\n".join(self._chunks)


_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def _is_public_host(hostname: str) -> bool:
    if not hostname or hostname.lower() in {"localhost"}:
        return False
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return False
    return True


def _fetch(url: str, *, timeout: float = 10.0) -> tuple[int, str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported scheme: {parsed.scheme}")
    if not _is_public_host(parsed.hostname or ""):
        raise ValueError("refusing non-public or unresolved host (SSRF guard)")
    req = Request(
        url,
        headers={"User-Agent": "OM-AI-Operating-Brain/0.3 (+authorized-fetch)"},
        method="GET",
    )
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — scheme/host gated above
        raw = resp.read(2_000_000)
        ctype = (resp.headers.get("Content-Type") or "").lower()
        status = getattr(resp, "status", 200) or 200
        charset = "utf-8"
        if "charset=" in ctype:
            charset = ctype.split("charset=", 1)[1].split(";")[0].strip() or "utf-8"
        text = raw.decode(charset, errors="replace")
        return int(status), ctype, text


def _html_to_text(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)
    return p.text()


def crawl(
    seed_url: str,
    *,
    max_pages: int = 1,
    same_host_only: bool = True,
    timeout: float = 10.0,
) -> list[CrawlPage]:
    """Fetch ``seed_url`` and optionally a few same-host links from that page."""
    pages: list[CrawlPage] = []
    seen: set[str] = set()
    queue = [seed_url]
    seed_host = urlparse(seed_url).netloc

    while queue and len(pages) < max(1, max_pages):
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            status, ctype, body = _fetch(url, timeout=timeout)
        except (ValueError, HTTPError, URLError, TimeoutError, OSError) as exc:
            pages.append(
                CrawlPage(url=url, text=f"[OM crawler] fetch failed: {exc}", status=0, stub=False)
            )
            continue
        if "html" in ctype or body.lstrip().startswith("<"):
            text = _html_to_text(body)
            if same_host_only and len(pages) + len(queue) < max_pages:
                for href in _HREF_RE.findall(body)[:50]:
                    abs_url = urljoin(url, href.split("#", 1)[0])
                    if urlparse(abs_url).netloc != seed_host:
                        continue
                    if abs_url not in seen:
                        queue.append(abs_url)
        else:
            text = body[:200_000]
        pages.append(CrawlPage(url=url, text=text, status=status, stub=False))
    return pages


def crawl_stub(seed_url: str, *, max_pages: int = 1) -> list[CrawlPage]:
    """Backward-compatible alias — now performs a real guarded fetch."""
    return crawl(seed_url, max_pages=max_pages)
