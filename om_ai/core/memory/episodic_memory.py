class EpisodicMemory:


    def __init__(
        self,
        store
    ):

        self.store=store



    def record(
        self,
        event
    ):

        self.store.save(
            "episode",
            event,
            3
        )