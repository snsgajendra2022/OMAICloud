class ToolDecisionEngine:

    def decide(
        self,
        intent_state
    ):

        if not intent_state.requires_tool:
            return {
                "use_tool": False,
                "tool": None
            }

        return {
            "use_tool": True,
            "tool": intent_state.tool_name
        }