"""Streaming helpers — chunk text for SSE / progressive UI."""
from __future__ import annotations

from typing import Iterator

from .formatter import ResponseBlock, reply_to_blocks, blocks_to_markdown


def chunk_text_for_stream(text: str, *, chunk_chars: int = 24) -> Iterator[str]:
    """Yield progressive prefixes (for simulated token stream of formatted text)."""
    s = text or ""
    if not s:
        return
    n = max(4, int(chunk_chars))
    for i in range(n, len(s) + 1, n):
        yield s[:i]
    if len(s) % n:
        yield s


def iter_block_stream(text: str, *, intent: str = "chat") -> Iterator[str]:
    """Yield markdown that grows one response block at a time (JARVIS-style)."""
    blocks = reply_to_blocks(text, intent=intent)
    acc: list[ResponseBlock] = []
    for b in blocks:
        acc.append(b)
        yield blocks_to_markdown(acc)
