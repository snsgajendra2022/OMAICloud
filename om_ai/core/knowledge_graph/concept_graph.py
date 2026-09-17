from __future__ import annotations


from .knowledge_node import KnowledgeNode
from .knowledge_edge import KnowledgeEdge



class ConceptGraph:
    """
    Main OM Knowledge Graph.

    Stores:

    Concepts
    Relationships
    Dependencies
    """


    def __init__(self):

        self.nodes: dict[str, KnowledgeNode] = {}

        self.edges: list[KnowledgeEdge] = []



    def add_node(
        self,
        node: KnowledgeNode
    ):

        self.nodes[node.id] = node



    def add_edge(
        self,
        edge: KnowledgeEdge
    ):

        self.edges.append(edge)



    def get_node(
        self,
        node_id: str
    ):

        return self.nodes.get(
            node_id
        )



    def remove_node(
        self,
        node_id: str
    ):

        if node_id in self.nodes:

            del self.nodes[node_id]



        self.edges = [

            e for e in self.edges

            if e.source != node_id

            and e.target != node_id

        ]



    def get_related_nodes(
        self,
        node_id: str
    ):

        result = []


        for edge in self.edges:

            if edge.source == node_id:

                result.append(
                    self.nodes.get(
                        edge.target
                    )
                )


            elif edge.target == node_id:

                result.append(
                    self.nodes.get(
                        edge.source
                    )
                )


        return [

            x for x in result

            if x

        ]



    def export(self):

        return {

            "nodes":[

                n.to_dict()

                for n in self.nodes.values()

            ],

            "edges":[

                e.to_dict()

                for e in self.edges

            ]

        }