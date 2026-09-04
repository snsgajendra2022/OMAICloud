"""Upgrade PermissionChecker to use ActionPermissionGate (STEP 86)."""
from __future__ import annotations


class PermissionChecker:
    def check(self, tool_name: str, request: str) -> dict:
        try:
            from om_ai.tools.intelligence.permission_gate import ActionPermissionGate

            v = ActionPermissionGate().check(tool_name, request or "")
            return {
                "tool": tool_name,
                "allowed": v.allowed,
                "reason": v.reason,
                "risk": v.risk,
                "requires_approval": v.requires_approval,
            }
        except Exception:
            return {
                "tool": tool_name,
                "allowed": True,
                "reason": "fallback_allow",
            }
