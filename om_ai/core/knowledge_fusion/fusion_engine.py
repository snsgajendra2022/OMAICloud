from .retriever import KnowledgeRetriever

from .context_ranker import ContextRanker

from .knowledge_selector import KnowledgeSelector



class KnowledgeFusionEngine:


    def __init__(self):

        self.retriever = KnowledgeRetriever()

        self.ranker = ContextRanker()

        self.selector = KnowledgeSelector()



    def process(
        self,
        query
    ):


        data = self.retriever.retrieve(
            query
        )


        ranked = self.ranker.rank(
            []
        )


        return self.selector.select(
            {
                "retrieved":
                    data,

                "ranked":
                    ranked
            }
        )