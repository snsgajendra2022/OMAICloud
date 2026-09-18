class IntelligenceSelector:


    def select(
        self,
        models,
        limit:int=3
    ):


        return models[:limit]