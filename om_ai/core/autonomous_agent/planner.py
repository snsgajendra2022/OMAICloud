from __future__ import annotations
from typing import Any

class Planner:
    def plan(self, goal: dict[str, Any]) -> dict[str, Any]:
        g = goal.get("goal") or "assist"
        catalog = {
            "continue_om_work": [
                {"id": "locate_workspace", "action": "find_path"},
                {"id": "open_editor", "action": "launch_app", "app": "Visual Studio Code"},
                {"id": "recall_focus", "action": "memory_recall"},
            ],
            "open_editor": [
                {"id": "launch", "action": "launch_app", "app": "Visual Studio Code"},
            ],
            "debug_issue": [
                {"id": "collect", "action": "gather_context"},
                {"id": "hypothesize", "action": "reason"},
                {"id": "fix", "action": "propose_patch"},
            ],
            "inspect_environment": [
                {"id": "observe", "action": "vision_or_files"},
                {"id": "report", "action": "summarize"},
            ],
            "assist": [
                {"id": "respond", "action": "converse"},
            ],
        }
        steps = catalog.get(g, catalog["assist"])
        return {"goal": g, "steps": steps, "requires_permission": g in {"continue_om_work", "open_editor"}}
