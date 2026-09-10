"""Decision stub used by cognitive package exports."""


class DecisionEngine:
    def decide(self, *args, **kwargs):
        return {"decision": "continue", "args": args, "kwargs": kwargs}
