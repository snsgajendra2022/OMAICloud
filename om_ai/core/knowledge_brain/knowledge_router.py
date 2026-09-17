from __future__ import annotations


from .knowledge_context import KnowledgeContext

from .knowledge_confidence import KnowledgeConfidence



class KnowledgeRouter:


    def __init__(
        self,
        graph=None,
        memory=None
    ):

        self.graph = graph

        self.memory = memory

        self.confidence_engine = (
            KnowledgeConfidence()
        )



    def route(
        self,
        query:str
    ):


        concepts=[]

        nodes=[]


        if self.memory:


            memory_results = (
                self.memory.search(
                    query
                )
            )


            if memory_results:

                concepts.extend(
                    [
                        "memory_match"
                    ]
                )



        if self.graph:


            for node in self.graph.nodes.values():

                name = getattr(
                    node,
                    "name",
                    ""
                )


                if name.lower() in query.lower():

                    concepts.append(
                        name
                    )

                    nodes.append(
                        node
                    )



        confidence = (
            self.confidence_engine.calculate(
                len(concepts)
            )
        )



        return KnowledgeContext(

            query=query,

            concepts=concepts,

            matched_nodes=nodes,

            confidence=confidence,

            knowledge_found=confidence >= 0.5,

            missing_information=[]

        )