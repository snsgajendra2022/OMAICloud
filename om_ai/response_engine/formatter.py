"""Structure raw model / fallback text into readable assistant blocks."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ResponseBlock:
    type: str
    content: str
    icon: str = ""
    items: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not d.get("items"):
            d.pop("items", None)
        if not d.get("icon"):
            d.pop("icon", None)
        return d


_BULLET = re.compile(r"^\s*[-*•✅✓]\s+(.+)$")
_NUMBER = re.compile(r"^\s*\d+[.)]\s+(.+)$")
_HEADING = re.compile(r"^\s{0,3}(#{1,3})\s+(.+)$")


def reply_to_blocks(text: str, *, intent: str = "chat") -> list[ResponseBlock]:
    raw = (text or "").strip()
    if not raw:
        return [ResponseBlock(type="info", icon="💬", content="(empty reply)")]

    # Already well-structured markdown with multiple sections — keep as one body
    if raw.count("\n## ") >= 1 or raw.count("\n### ") >= 2:
        return [ResponseBlock(type="markdown", content=raw)]

    lines = [ln.rstrip() for ln in raw.splitlines()]
    blocks: list[ResponseBlock] = []
    para: list[str] = []
    list_items: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            body = " ".join(p.strip() for p in para if p.strip()).strip()
            if body:
                blocks.append(ResponseBlock(type="paragraph", content=body))
            para = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.append(
                ResponseBlock(type="list", icon="✅", content="", items=list(list_items))
            )
            list_items = []

    for ln in lines:
        if not ln.strip():
            flush_list()
            flush_para()
            continue
        hm = _HEADING.match(ln)
        if hm:
            flush_list()
            flush_para()
            blocks.append(ResponseBlock(type="heading", icon="📌", content=hm.group(2).strip()))
            continue
        bm = _BULLET.match(ln) or _NUMBER.match(ln)
        if bm:
            flush_para()
            list_items.append(bm.group(1).strip())
            continue
        flush_list()
        para.append(ln)

    flush_list()
    flush_para()

    if not blocks:
        blocks = [ResponseBlock(type="paragraph", content=raw)]

    # Greeting polish
    if intent == "greeting" and blocks and blocks[0].type == "paragraph":
        if not blocks[0].content.startswith(("👋", "Hey", "Hello", "Hi")):
            blocks[0] = ResponseBlock(
                type="greeting",
                icon="👋",
                content=blocks[0].content,
            )

    return blocks


def blocks_to_markdown(blocks: list[ResponseBlock]) -> str:
    parts: list[str] = []
    for b in blocks:
        icon = (b.icon + " ") if b.icon else ""
        if b.type == "heading":
            parts.append(f"## {icon}{b.content}".rstrip())
        elif b.type == "greeting":
            parts.append(f"{icon}{b.content}".strip())
        elif b.type == "list" and b.items:
            parts.append(icon.rstrip() or "✅")
            for it in b.items:
                parts.append(f"- {it}")
        elif b.type == "markdown":
            parts.append(b.content)
        else:
            parts.append(f"{icon}{b.content}".strip())
        parts.append("")
    return "\n".join(parts).strip()


def format_assistant_reply(
    text: str,
    *,
    intent: str = "chat",
    enhance: bool = True,
) -> str:
    """Normalize spacing and lightly structure a reply for the chat UI."""
    raw = (text or "").strip()
    if not raw:
        return raw
    # Collapse extreme whitespace but keep paragraph breaks
    raw = re.sub(r"[ \t]+\n", "\n", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)

    if not enhance:
        return raw

    # If already has markdown structure, only normalize
    if re.search(r"(?m)^#{1,3}\s|```", raw) or raw.count("\n- ") >= 2:
        return raw

    blocks = reply_to_blocks(raw, intent=intent)
    if len(blocks) <= 1 and blocks and blocks[0].type in {"paragraph", "markdown"}:
        return raw
    return blocks_to_markdown(blocks)
