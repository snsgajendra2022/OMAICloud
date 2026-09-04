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
        text: str
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


    def process(
        self,
        entities,
        source: str = "text",
    ):
        """Adapter for PDF / document semantic callers.

        Accepts a dict of extracted entities (or free text) and returns a
        graph-shaped payload compatible with ``om_ai.knowledge.graph``.
        """
        if isinstance(entities, str):
            return self.learn(entities)

        data = entities if isinstance(entities, dict) else {}
        # Prefer shared graph builders when available
        try:
            from om_ai.knowledge.graph.engine import KnowledgeGraphEngine as GraphEngine

            return GraphEngine().process(data, source)
        except Exception:
            # Fallback: learn from a synthetic text blob
            blob = " ".join(f"{k} {v}" for k, v in data.items())
            learned = self.learn(blob) if blob.strip() else {"entities": 0, "relations": 0}
            return {
                "entities": [
                    {"name": str(v), "entity_type": str(k), "source": source}
                    for k, v in data.items()
                ],
                "relations": [],
                "store_stats": learned,
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