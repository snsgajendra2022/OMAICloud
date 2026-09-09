class LearningAnalyzer:



    def analyze(
        self,
        experience
    ):


        response = (
            experience.response.lower()
        )


        score = 0.5


        if len(response) > 50:

            score += 0.2


        if "error" in response:

            score -= 0.3


        if "i don't know" in response:

            score -= 0.1


        score = max(
            0,
            min(score,1)
        )


        experience.score = score


        if score >= 0.7:

            experience.result="success"

        else:

            experience.result="needs_improvement"



        return experience