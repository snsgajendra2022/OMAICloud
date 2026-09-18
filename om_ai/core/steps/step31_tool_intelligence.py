"""STEP 31 — OM Tool Intelligence."""
from om_ai.core.tool_intelligence import ToolIntelligence, run_tool_intelligence

__all__ = ["ToolIntelligence", "run_tool_intelligence", "Step31ToolIntelligence"]


class Step31ToolIntelligence(ToolIntelligence):
    step = 31
