class TaskDelegator:



    def assign(
        self,
        task,
        agents
    ):


        task_lower = task.lower()


        if "code" in task_lower:

            return "coding"


        if "research" in task_lower:

            return "research"


        if "security" in task_lower:

            return "security"


        return "general"