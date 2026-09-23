"""Execution guard — think before acting; ask permission for side effects."""
from __future__ import annotations

from typing import Any


class ExecutionGuard:
    def check(self, policy: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = policy or {}
        kind = str(policy.get("kind") or "none")

        if kind == "search":
            return {
                "allowed": True,
                "requires_permission": False,
                "execute": "search_only",
                "prompt": "",
                "message": "Search and summarize. Do not open browser.",
            }

        if kind in {"open", "destructive"} or policy.get("requires_permission"):
            prompt = (
                "I can open it. Permission required — proceed?"
                if kind == "open"
                else "This can change your system. Permission required — proceed?"
            )
            return {
                "allowed": False,
                "requires_permission": True,
                "execute": "wait",
                "prompt": prompt,
                "message": prompt,
            }

        return {
            "allowed": True,
            "requires_permission": False,
            "execute": "none",
            "prompt": "",
            "message": "",
        }

    def after_permission(self, approved: bool, policy: dict[str, Any] | None = None) -> dict[str, Any]:
        if not approved:
            return {"allowed": False, "execute": "cancel", "message": "Okay — cancelled."}
        return {
            "allowed": True,
            "requires_permission": False,
            "execute": str((policy or {}).get("kind") or "open"),
            "message": "Proceeding.",
        }
