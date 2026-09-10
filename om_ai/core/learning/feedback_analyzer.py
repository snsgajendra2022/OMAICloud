class FeedbackAnalyzer:


    def analyze(
        self,
        question,
        answer
    ):


        issues=[]


        if not answer:

            issues.append(
                "empty_response"
            )


        if len(answer)<20:

            issues.append(
                "too_short"
            )


        return {

            "issues":issues,

            "score":
                1.0
                if not issues
                else 0.5

        }