class ReasoningFusion:

    def combine(self, reasoning_outputs: list):
        return {
            "strategies": reasoning_outputs,
            "count": len(reasoning_outputs or []),
        }
