class ConfidenceEngine:


    def calculate(
        self,
        intent,
        entities
    ):


        score=0.5


        if intent!="unknown":

            score +=0.3


        if entities:

            score +=0.2


        return min(
            score,
            1.0
        )