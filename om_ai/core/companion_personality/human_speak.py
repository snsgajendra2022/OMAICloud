"""Dynamic spoken lines for companion actions — composed live, not a script library."""
from __future__ import annotations

import re
from typing import Any


def locale_from(text: str) -> str:
    low = (text or "").lower()
    if re.search(
        r"[\u0900-\u097F]|\b(hai|hain|kya|tum|nahi|karo|batao|mujhe|ji|theek|haan)\b",
        low,
    ):
        return "hi"
    return "en"


def action_ack(
    *,
    kind: str,
    query: str = "",
    user_message: str = "",
    address: str = "Sir",
) -> str:
    """Natural spoken commitment before/after an action."""
    hi = locale_from(user_message) == "hi"
    q = (query or "").strip().strip(" .")
    addr = address or "Sir"

    if kind in {"time", "clock"}:
        return f"Theek hai {addr}, time dekh ke bataata hun." if hi else f"Checking the time for you, {addr}."

    if kind in {"google", "search", "browser"}:
        if hi:
            if q:
                return f"Theek hai bhai, main '{q}' dhoondh ke bataata hun — browser nahi kholunga jab tak tum 'go' na bolo."
            return f"Theek hai bhai, main search karta hun aur jo mila woh bataunga."
        if q:
            return f"Alright brother — I'll search “{q}” and tell you what I find. I won't open the browser unless you say go."
        return f"Alright brother — searching now. I'll report what I find."

    if kind in {"search_open"}:
        if hi:
            return f"Theek hai bhai, Google khol raha hun{(' — ' + q) if q else ''}."
        return f"Opening Google for you, brother{(' — ' + q) if q else ''}."

    if kind in {"weather", "mausam"}:
        return f"Theek hai {addr}, mausam check karta hun." if hi else f"Checking the weather for you, {addr}."

    if kind in {"youtube", "play"}:
        if hi:
            return f"Theek hai {addr}, YouTube pe dhundhta hun." if q else f"Theek hai {addr}, open kar raha hun."
        return f"On it {addr} — pulling that up on YouTube." if q else f"Opening that now, {addr}."

    if kind in {"app", "open"}:
        return f"Theek hai {addr}, khol raha hun." if hi else f"Opening that for you, {addr}."

    if kind in {"volume", "mute"}:
        return f"Theek hai {addr}." if hi else f"Done, {addr}."

    return f"Theek hai {addr}." if hi else f"On it, {addr}."


def thinking_presence() -> str:
    """HUD should stay quiet — no robotic status chrome."""
    return ""


def strip_robot_ui(text: str) -> str:
    t = (text or "").strip()
    for bad in (
        "Got it — thinking",
        "Got it — thinking…",
        "Got it...",
        "Understanding request",
        "Companion ready",
        "Getting the gist",
        "Composing reply",
        "Choosing approach",
    ):
        if t.lower().startswith(bad.lower()):
            return ""
    return t
