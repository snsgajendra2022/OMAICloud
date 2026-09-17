from .research_task import ResearchTask

from .research_memory import ResearchMemory



class ResearchEngine:


    def __init__(self):

        self.memory = ResearchMemory()



    def create(
        self,
        query,
        reason="knowledge_gap"
    ):


        task = ResearchTask(

            query=query,

            reason=reason,

            priority=0.8

        )


        self.memory.add(
            task
        )


        return task