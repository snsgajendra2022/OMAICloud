"""OM AI Response Experience Engine — format, markdown, style, streaming helpers.

This is the Experience Layer (not the foundation model). Even a small OM model
can deliver ChatGPT-style presentation when the UI + formatter cooperate.
"""
from __future__ import annotations

from .formatter import ResponseBlock, format_assistant_reply, reply_to_blocks, blocks_to_markdown
from .emotion_style import style_opening, EXPERIENCE_PHASES
from .markdown_parser import markdown_to_safe_html
from .stream_manager import chunk_text_for_stream, iter_block_stream

__all__ = [
    "ResponseBlock",
    "format_assistant_reply",
    "reply_to_blocks",
    "blocks_to_markdown",
    "style_opening",
    "EXPERIENCE_PHASES",
    "markdown_to_safe_html",
    "chunk_text_for_stream",
    "iter_block_stream",
]
