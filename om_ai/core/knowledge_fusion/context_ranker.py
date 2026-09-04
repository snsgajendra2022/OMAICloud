class ContextRanker:


    def rank(
        self,
        items
    ):


        return sorted(
            items,
            key=lambda x:
            x.get(
                "importance",
                0
            ),
            reverse=True
        )