from __future__ import annotations

import re

from bs4 import BeautifulSoup


class ContentExtractor:

    def extract(
        self,
        html: str,
    ) -> str:

        if not html:
            return ""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "iframe",
                "nav",
                "footer",
            ]
        ):
            tag.decompose()

        text = soup.get_text(
            separator="\n"
        )

        lines = []

        for line in text.splitlines():

            line = re.sub(
                r"\s+",
                " ",
                line,
            ).strip()

            if len(line) < 2:
                continue

            lines.append(line)

        return "\n".join(lines)