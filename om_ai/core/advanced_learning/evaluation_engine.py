class EvaluationEngine:



    def evaluate(
        self,
        response
    ):


        score=0.5


        if len(response)>100:

            score +=0.2


        if "solution" in response.lower():

            score +=0.1


        return {

            "score":
            min(score,1),


            "missing_context":
            False

        }