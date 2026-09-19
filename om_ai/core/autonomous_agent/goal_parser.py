from __future__ import annotations
import re
from typing import Any

class GoalParser:
    def parse(self, text: str) -> dict[str, Any]:
        low = (text or "").lower()
        goal = "assist"
        steps_hint = []
        if re.search(r"(?i)continue.*(om|work|project)", low):
            goal = "continue_om_work"
            steps_hint = ["find_project", "open_editor", "restore_context"]
        elif re.search(r"(?i)open.*(vs\s*code|code|editor)", low):
            goal = "open_editor"
            steps_hint = ["resolve_app", "launch"]
        elif re.search(r"(?i)(fix|debug|error|model issue)", low):
            goal = "debug_issue"
            steps_hint = ["locate_error", "inspect", "propose_fix"]
        elif re.search(r"(?i)check.*(screen|browser|files)", low):
            goal = "inspect_environment"
            steps_hint = ["observe", "summarize"]
        return {"goal": goal, "raw": text, "hints": steps_hint, "confidence": 0.7 if steps_hint else 0.45}
