from __future__ import annotations
from typing import Any

class ScreenReader:
    def snapshot(self) -> dict[str, Any]:
        # Permission-gated; do not capture without explicit allow
        return {
            "ok": False,
            "reason": "screen_capture_requires_permission",
            "hint": "Enable via companion permissions, then reconnect vision runtime.",
        }

    def read(self) -> dict[str, Any]:
        return self.snapshot()
