from .context_memory import ContextMemory
from .context_retriever import ContextRetriever
from .context_ranker import ContextRanker



class ContextManager:


    def __init__(self):

        self.memory=ContextMemory()

        self.retriever=ContextRetriever()

        self.ranker=ContextRanker()



    def remember(
        self,
        role,
        message
    ):

        self.memory.add(
            role,
            message
        )



    def get_context(
        self,
        query
    ):


        data=self.retriever.search(

            self.memory.all(),

            query

        )


        return self.ranker.rank(
            data
        )