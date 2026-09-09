class AnswerVerifier:

    def verify(
        self,
        user_message,
        response,
        plan
    ):

        return {
            "answered":
                bool(response.strip()),

            "response_length":
                len(response),

            "plan_completed":
                True
        }