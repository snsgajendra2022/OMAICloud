"""
OM Knowledge Graph Engine
"""


from .extractor import ConceptExtractor

from .graph_store import GraphStore





class KnowledgeGraphEngine:



    def __init__(self):


        self.extractor=ConceptExtractor()

        self.store=GraphStore()




    def learn(

        self,

        text:str

    ):


        graph=self.extractor.extract(

            text

        )


        result=self.store.add(

            graph

        )


        return {


            "entities":

                len(result["entities"]),


            "relations":

                len(result["relations"])

        }




    def search(

        self,

        concept:str

    ):


        graph=self.store.load()



        results=[]


        for relation in graph["relations"]:


            if concept.lower() in (

                relation["source"].lower()

                +

                relation["target"].lower()

            ):


                results.append(
                    relation
                )


        return results