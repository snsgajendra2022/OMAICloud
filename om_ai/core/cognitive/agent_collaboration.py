class AgentCollaboration:


    def route(
        self,
        task
    ):


        task=task.lower()


        if "code" in task:

            return "coding_agent"


        if "research" in task:

            return "research_agent"


        if "document" in task:

            return "document_agent"


        return "general_agent"