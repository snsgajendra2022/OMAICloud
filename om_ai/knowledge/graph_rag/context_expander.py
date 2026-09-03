"""
OM Knowledge Graph RAG Expansion Engine
"""


from .graph_retriever import GraphRetriever

from .merger import ContextMerger





class GraphRAGExpander:



    def __init__(self):


        self.graph = GraphRetriever()

        self.merger = ContextMerger()




    def expand(

        self,

        question:str,

        vector_results:list

    ):



        graph_results = self.graph.search(

            question

        )



        return self.merger.merge(

            vector_results,

            graph_results

        )