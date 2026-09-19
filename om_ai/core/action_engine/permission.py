from __future__ import annotations

class PermissionGate:
    def allow(self, action: str) -> bool:
        # Plan-only by default — destructive actions need explicit grant
        return action in {"analyze", "read", "plan", "summarize", "check"}
