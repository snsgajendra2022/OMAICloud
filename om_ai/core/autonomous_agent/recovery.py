from __future__ import annotations
from typing import Any

class Recovery:
    def recover(self, failed_step: dict[str, Any], error: str = "") -> dict[str, Any]:
        return {
            "retry": True,
            "strategy": "simplify_and_retry",
            "message": f"Recovering from {failed_step.get('id')}: {error or 'unknown'}",
        }
