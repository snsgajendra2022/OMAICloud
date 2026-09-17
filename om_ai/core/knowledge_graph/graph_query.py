from __future__ import annotations



class GraphQuery:
    """
    Query interface for OM knowledge graph.
    """


    def __init__(
        self,
        graph
    ):

        self.graph = graph



    def search(
        self,
        text: str
    ):

        text = text.lower()


        result=[]


        for node in self.graph.nodes.values():

            if text in node.name.lower():

                result.append(node)


        return result



    def related(
        self,
        node_id: str
    ):

        return self.graph.get_related_nodes(
            node_id
        )