class QualityController:



    def evaluate(
        self,
        response:str
    ):


        if not response:

            return {

                "approved":
                False,

                "score":
                0

            }


        length_score = min(
            len(response)/500,
            1
        )


        return {


            "approved":

            length_score > 0.2,


            "score":

            round(
                length_score,
                2
            )

        }