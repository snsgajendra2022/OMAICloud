"""Learning memory alias → improvement_memory."""
from __future__ import annotations

from typing import Any

from .improvement_memory import ImprovementMemory


class LearningMemory(ImprovementMemory):
    def record(self, row: dict[str, Any]) -> None:
        if hasattr(self, "remember"):
            self.remember(row)
        else:
            try:
                from om_ai.core.self_learning import note_turn

                note_turn(
                    str(row.get("user") or ""),
                    str(row.get("answer") or ""),
                    emotion=str(row.get("emotion") or ""),
                )
            except Exception:
                pass
