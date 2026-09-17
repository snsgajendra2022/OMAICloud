class ContextRanker:



    def rank(
        self,
        contexts
    ):


        return sorted(

            contexts,

            key=lambda x:
                len(
                    x["content"]
                ),

            reverse=True

        )