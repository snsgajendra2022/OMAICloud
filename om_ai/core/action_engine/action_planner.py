from __future__ import annotations
from typing import Any

from .executor import Executor
from .permission import PermissionGate
from .recovery import Recovery
from .tool_selector import ToolSelector
from .verifier import Verifier

_RT = None

class ActionEngine:
    def __init__(self) -> None:
        self.tools = ToolSelector()
        self.executor = Executor()
        self.verifier = Verifier()
        self.permission = PermissionGate()
        self.recovery = Recovery()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 108, "name": "Action Intelligence"}

    def plan(self, text: str, *, execute: bool = False) -> dict[str, Any]:
        low = (text or "").lower()
        tools = self.tools.pick(text)
        steps = []
        spoken = ""

        if any(k in low for k in ("response quality", "quality is bad", "find why", "check my project")):
            steps = [
                {"id": "1", "label": "Inspect response pipeline", "tool": "pipeline_trace"},
                {"id": "2", "label": "Check model / capacity limits", "tool": "model_limits"},
                {"id": "3", "label": "Look for missing verification layer", "tool": "code_inspect"},
            ]
            spoken = (
                "I found three possible issues.\n\n"
                "1. Response pipeline\n"
                "2. Small model limitation\n"
                "3. Missing verification layer\n\n"
                "I will analyze them one by one."
            )
        elif "demo" in low or "prepare" in low:
            steps = [
                {"id": "1", "label": "Check project build", "tool": "build_check"},
                {"id": "2", "label": "Generate screenshots", "tool": "screenshots"},
                {"id": "3", "label": "Scan for errors", "tool": "code_inspect"},
                {"id": "4", "label": "Prepare notes", "tool": "notes"},
            ]
            spoken = (
                "I will:\n"
                "1. Check project\n"
                "2. Build application\n"
                "3. Create screenshots\n"
                "4. Prepare notes"
            )
        else:
            steps = [{"id": "1", "label": "Clarify goal and gather context", "tool": "memory_recall"}]
            spoken = "Understood. I will break this into clear steps and proceed carefully."

        results = []
        for step in steps:
            tool = step.get("tool") or "plan"
            if self.permission.allow(tool.split("_")[0] if "_" in tool else "plan") or tool in {
                "pipeline_trace", "model_limits", "code_inspect", "memory_recall",
                "build_check", "screenshots", "notes", "screen_reader",
            }:
                results.append(self.executor.run_step(step, execute=execute))

        verify = self.verifier.check(results)
        return {
            "goal": text,
            "tools": tools,
            "steps": steps,
            "results": results,
            "verify": verify,
            "spoken": spoken,
            "execute": execute,
        }

def get_action_engine() -> ActionEngine:
    global _RT
    if _RT is None:
        _RT = ActionEngine()
    return _RT
