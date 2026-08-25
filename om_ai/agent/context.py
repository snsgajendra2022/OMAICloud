"""Tiny-context conversation packing for OM-1.0 (max_seq_len often 128)."""
from __future__ import annotations

from typing import Any


def pack_messages_for_tiny_context(
    messages: list[dict[str, Any]],
    *,
    max_turns: int = 4,
    max_chars_per_turn: int = 220,
) -> list[dict[str, str]]:
    """Keep recent user/assistant turns; trim long blobs.

    Context accounting for small windows: prefer recent dialogue so OM
    "remembers" the thread without overflowing OM-1.0's tiny context.
    """
    cleaned: list[dict[str, str]] = []
    for m in messages or []:
        role = str(m.get("role") or "user").strip().lower()
        if role not in {"system", "user", "assistant"}:
            role = "user"
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        if len(content) > max_chars_per_turn and role != "system":
            content = content[: max_chars_per_turn - 1].rstrip() + "…"
        cleaned.append({"role": role, "content": content})

    system = [m for m in cleaned if m["role"] == "system"]
    non_system = [m for m in cleaned if m["role"] != "system"]
    if len(non_system) > max_turns * 2:
        non_system = non_system[-(max_turns * 2) :]
    lead = system[:1]
    return lead + non_system


def budget_hint(extra: str, *, max_chars: int = 180) -> str:
    s = (extra or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"
