class ModelRouter:


    def __init__(
        self,
        registry,
        capability
    ):

        self.registry = registry

        self.capability = capability



    def route(
        self,
        task:str
    ):


        ranked=[]


        for model in self.registry.available_models():


            score = self.capability.score(
                model,
                task
            )


            ranked.append(
                (
                    score,
                    model
                )
            )



        ranked.sort(
            key=lambda x:x[0],
            reverse=True
        )


        return [

            item[1]

            for item in ranked

            if item[0] > 0

        ]