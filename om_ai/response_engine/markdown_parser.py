"""Lightweight markdown → safe HTML (server-side helper; UI has its own renderer)."""
from __future__ import annotations

import html
import re


def markdown_to_safe_html(text: str) -> str:
    s = html.escape(text or "")
    blocks: list[str] = []

    def _code(m: re.Match[str]) -> str:
        lang = m.group(1) or ""
        code = m.group(2)
        i = len(blocks)
        blocks.append(
            f'<pre><code class="language-{html.escape(lang)}">{code}</code></pre>'
        )
        return f"\x00CB{i}\x00"

    s = re.sub(r"```(\w*)\n([\s\S]*?)```", _code, s)
    s = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", s)
    s = re.sub(r"^### (.+)$", r"<h3>\1</h3>", s, flags=re.M)
    s = re.sub(r"^## (.+)$", r"<h2>\1</h2>", s, flags=re.M)
    s = re.sub(r"^# (.+)$", r"<h1>\1</h1>", s, flags=re.M)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?m)^[-*] (.+)$", r"<li>\1</li>", s)
    s = re.sub(r"(?:<li>.*?</li>\n?)+", lambda m: "<ul>" + m.group(0) + "</ul>", s)
    s = s.replace("\n", "<br>")
    for i, b in enumerate(blocks):
        s = s.replace(f"\x00CB{i}\x00", b)
    return s
