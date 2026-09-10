from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests


@dataclass
class PageReadResult:
    url: str
    status_code: int
    content_type: str
    text: str
    headers: dict[str, Any]


class PageReader:

    def __init__(
        self,
        *,
        timeout: int = 15,
        max_bytes: int = 2_000_000,
        user_agent: str = "OM-AI-Research/1.0",
    ) -> None:

        self.timeout = timeout
        self.max_bytes = max_bytes
        self.user_agent = user_agent

    def read(
        self,
        url: str,
    ) -> PageReadResult | None:

        if not self._allowed_url(url):
            return None

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    "User-Agent":
                        self.user_agent
                },
                allow_redirects=True,
            )

            content = response.content[
                : self.max_bytes
            ]

            text = content.decode(
                response.encoding
                or "utf-8",
                errors="replace",
            )

            return PageReadResult(
                url=response.url,
                status_code=response.status_code,
                content_type=response.headers.get(
                    "content-type",
                    "",
                ),
                text=text,
                headers=dict(response.headers),
            )

        except Exception:
            return None

    @staticmethod
    def _allowed_url(
        url: str,
    ) -> bool:

        try:
            parsed = urlparse(url)

            return (
                parsed.scheme in {
                    "http",
                    "https",
                }
                and bool(parsed.netloc)
            )
        except Exception:
            return False