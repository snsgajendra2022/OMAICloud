class ExperienceMemory:


    def __init__(
        self,
        store
    ):

        self.store=store



    def save_experience(
        self,
        experience
    ):

        self.store.save(
            "experience",
            experience,
            5
        )