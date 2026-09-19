from __future__ import annotations
from typing import Any

class MonitoringEngine:
    def health_hints(self) -> list[str]:
        hints = []
        try:
            from pathlib import Path
            if not Path("artifacts/checkpoints").exists():
                hints.append("No checkpoints folder spotted.")
        except Exception:
            pass
        return hints
