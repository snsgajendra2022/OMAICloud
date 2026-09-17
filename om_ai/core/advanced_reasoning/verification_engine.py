class VerificationEngine:



    def verify(
        self,
        answer
    ):


        return {


            "valid":

                bool(answer.strip()),


            "confidence":

                0.8

        }