class FailureDetector:



    def detect(
        self,
        experience
    ):


        problems=[]


        if experience.score < 0.5:

            problems.append(
                "low_quality_response"
            )


        if not experience.response:

            problems.append(
                "empty_response"
            )


        if len(
            experience.response.split()
        ) < 3:

            problems.append(
                "insufficient_answer"
            )


        return problems