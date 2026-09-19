from __future__ import annotations

class ToolSelector:
    def pick(self, goal: str) -> list[str]:
        g = (goal or "").lower()
        tools = ["memory_recall"]
        if any(k in g for k in ("project", "response", "quality", "code", "bug")):
            tools += ["code_inspect", "pipeline_trace", "model_limits"]
        if "demo" in g:
            tools += ["build_check", "screenshots", "notes"]
        if "screen" in g:
            tools += ["screen_reader"]
        return tools
