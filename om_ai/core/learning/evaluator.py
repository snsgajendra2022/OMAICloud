class LearningEvaluator:


    def evaluate(
        self,
        experience
    ):


        score = 1


        if not experience["response"]:

            score = 0


        return {

            "score":
                score,

            "quality":
                "good"
                if score == 1
                else
                "poor"

        }