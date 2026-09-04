class LongTermMemory:


    def __init__(
        self,
        store
    ):

        self.store=store



    def remember(
        self,
        information
    ):


        self.store.save(
            "long_term",
            information,
            5
        )



    def recall(self):

        return self.store.search(
            "long_term"
        )