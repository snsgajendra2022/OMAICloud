class KnowledgeGraph:



    def __init__(self):

        self.graph={}



    def connect(
        self,
        concept,
        relation,
        target
    ):


        if concept not in self.graph:

            self.graph[concept]=[]


        self.graph[concept].append({

            "relation":
                relation,

            "target":
                target

        })



    def get(
        self,
        concept
    ):

        return self.graph.get(
            concept,
            []
        )