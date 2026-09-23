"""Detect canned solution-template replies that must never reach the user."""
from __future__ import annotations

import re

_STUB_SMELL = re.compile(
    r"(?is)("
    r"the issue may come from incorrect assumptions|"
    r"here'?s the direct path for\s*:|"
    r"solve\s*:\s*.{0,200}\b(understand|acknowledge|answer|next\s*step)\b|"
    r"clarify goal, then give a direct actionable answer|"
    r"the problem may be caused by environment or configuration|"
    r"the current approach may need redesign"
    r")"
)


def is_solution_stub(text: str) -> bool:
    """True for generic Solve:/assumption outline dumps."""
    t = (text or "").strip()
    if not t:
        return False
    if _STUB_SMELL.search(t):
        return True
    # Numbered outline that just echoes the user ask
    if re.search(r"(?i)\b(solve|fix|accomplish|understand)\s*:", t) and re.search(
        r"(?m)^\s*1\.\s+\w+", t
    ):
        if len(t) < 420 and t.count("\n") <= 8:
            return True
    return False
