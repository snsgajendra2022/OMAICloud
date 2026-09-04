class SemanticMemory:


    def __init__(
        self,
        store
    ):

        self.store=store



    def add_fact(
        self,
        fact
    ):

        self.store.save(
            "semantic",
            fact,
            4
        )