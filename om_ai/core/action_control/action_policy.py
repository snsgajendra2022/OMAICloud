"""Action policy — separate information search from side-effect actions."""
from __future__ import annotations

import re
from typing import Any


class ActionPolicy:
    """
    Search  → information only (no browser redirect)
    Open    → action (permission required)
    Delete  → destructive (permission required)
    """

    def classify(self, message: str) -> dict[str, Any]:
        text = (message or "").strip()
        low = text.lower()

        wants_open = bool(
            re.search(
                r"(?i)\b(go|open|kholo|khol|launch|navigate|redirect|take\s+me|"
                r"open\s+in\s+browser|show\s+in\s+browser)\b",
                low,
            )
        )
        is_search = bool(
            re.search(r"(?i)\b(search|google|khoj|research|look\s+up|find|dhundo)\b", low)
            or "search karo" in low
        )
        is_open_app = bool(
            re.search(r"(?i)\b(open|kholo|launch|start)\b", low)
            and not is_search
        )
        is_destructive = bool(
            re.search(r"(?i)\b(delete|remove|rm\b|erase|uninstall|format)\b", low)
        )

        if is_search and not wants_open:
            return {
                "kind": "search",
                "side_effect": False,
                "requires_permission": False,
                "may_open_browser": False,
                "reason": "information_request",
            }
        if is_search and wants_open:
            return {
                "kind": "open",
                "side_effect": True,
                "requires_permission": True,
                "may_open_browser": True,
                "reason": "user_asked_to_open",
            }
        if is_destructive:
            return {
                "kind": "destructive",
                "side_effect": True,
                "requires_permission": True,
                "may_open_browser": False,
                "reason": "destructive_action",
            }
        if is_open_app or wants_open:
            return {
                "kind": "open",
                "side_effect": True,
                "requires_permission": True,
                "may_open_browser": "http" in low or "www." in low or "browser" in low,
                "reason": "action_request",
            }
        return {
            "kind": "none",
            "side_effect": False,
            "requires_permission": False,
            "may_open_browser": False,
            "reason": "conversation",
        }
