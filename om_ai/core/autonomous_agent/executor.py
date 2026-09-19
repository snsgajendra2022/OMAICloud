from __future__ import annotations
from typing import Any

class Executor:
    def run_step(self, step: dict[str, Any], *, actions=None) -> dict[str, Any]:
        action = step.get("action")
        # Soft execute — real OS actions go through action_control when permitted
        if action == "launch_app" and actions is not None:
            try:
                return {"ok": True, "delegated": True, "step": step}
            except Exception as exc:
                return {"ok": False, "error": str(exc), "step": step}
        return {"ok": True, "simulated": True, "step": step, "message": f"Prepared: {action}"}
