"""Website crawl stub — placeholder for self-hosted ingestion."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrawlPage:
    url: str
    text: str
    stub: bool = True


def crawl_stub(seed_url: str, *, max_pages: int = 1) -> list[CrawlPage]:
    _ = max_pages
    return [
        CrawlPage(
            url=seed_url,
            text=f"[OM crawler stub] Would crawl from {seed_url}. Not implemented.",
            stub=True,
        )
    ]
