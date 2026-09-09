class SourceEvaluator:



    def evaluate(
        self,
        source
    ):


        score=0.5


        if source:

            score +=0.3


        return {

            "source":
                source,

            "confidence":
                min(score,1)

        }