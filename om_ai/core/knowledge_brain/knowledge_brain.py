from __future__ import annotations


from .knowledge_router import KnowledgeRouter

from .knowledge_memory import KnowledgeMemory



class KnowledgeBrain:


    def __init__(
        self,
        graph=None
    ):

        self.memory = KnowledgeMemory()


        self.router = KnowledgeRouter(

            graph=graph,

            memory=self.memory

        )



    def analyze(
        self,
        query:str
    ):


        context = (
            self.router.route(
                query
            )
        )


        return context



    def add(
        self,
        topic,
        data
    ):


        self.memory.store(
            topic,
            data
        )