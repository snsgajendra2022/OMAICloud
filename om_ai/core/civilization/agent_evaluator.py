class AgentEvaluator:



    def evaluate(
        self,
        result
    ):


        score=0.5


        if result:

            score +=0.3


        return {

            "score":
            min(score,1),


            "improve":
            score < 0.8

        }