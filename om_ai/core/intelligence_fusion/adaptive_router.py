class AdaptiveRouter:



    def __init__(
        self
    ):

        self.history={}



    def record(
        self,
        model,
        score
    ):

        self.history.setdefault(
            model,
            []
        ).append(
            score
        )



    def best(
        self
    ):


        result=None

        best_score=0


        for model,scores in self.history.items():

            avg=sum(scores)/len(scores)


            if avg > best_score:

                best_score=avg

                result=model



        return result