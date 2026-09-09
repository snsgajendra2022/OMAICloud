class SolutionPlanner:

    def create(self, analysis):
        goal = ""
        if isinstance(analysis, dict):
            goal = str(analysis.get("goal") or "")
        return self._steps(goal)

    def create_plan(self, analysis):
        return self.create(analysis)

    def _steps(self, goal: str):
        if goal == "creation":
            return [
                "Analyze requirement",
                "Select approach",
                "Execute solution",
                "Validate result",
            ]
        return [
            "Analyze requirement",
            "Select approach",
            "Execute solution",
            "Validate result",
        ]
