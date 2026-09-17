from __future__ import annotations



class DependencyResolver:
    """
    Finds learning prerequisites.
    """


    def __init__(
        self,
        graph
    ):

        self.graph = graph



    def resolve(
        self,
        concept_id: str
    ):

        dependencies = []


        visited = set()



        def walk(node):

            if node in visited:

                return


            visited.add(node)


            for edge in self.graph.edges:


                if (

                    edge.target == node

                    and

                    edge.relationship == "requires"

                ):

                    dependencies.append(
                        edge.source
                    )

                    walk(
                        edge.source
                    )



        walk(
            concept_id
        )


        return list(
            reversed(
                dependencies
            )
        )