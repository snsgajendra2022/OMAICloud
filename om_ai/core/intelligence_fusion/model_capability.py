class ModelCapability:


    def score(
        self,
        model,
        task:str
    ):

        score = 0


        for capability in model.capabilities:

            if capability.lower() in task.lower():

                score += 1


        return score