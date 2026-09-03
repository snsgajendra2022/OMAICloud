"""
OM Knowledge Graph Retriever

Finds related concepts from graph.
"""


from om_ai.knowledge_graph import KnowledgeGraphEngine





class GraphRetriever:



    def __init__(self):

        self.graph = KnowledgeGraphEngine()



    def search(

        self,

        query:str,

        limit:int = 5

    ):


        words = query.lower().split()


        results=[]


        for word in words:


            matches=self.graph.search(

                word

            )


            results.extend(matches)



        return results[:limit]