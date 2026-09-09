class QualityChecker:


    def validate(
        self,
        response: str
    ):


        if not response:

            return {
                "approved":False,
                "score":0
            }


        bad_tokens = [

            "�",
            "null",
            "undefined",
            "asdf"

        ]


        for token in bad_tokens:

            if token in response.lower():

                return {
                    "approved":False,
                    "score":0.1
                }


        words = len(
            response.split()
        )


        score = min(
            words / 100,
            1
        )


        return {

            "approved":True,

            "score":score

        }