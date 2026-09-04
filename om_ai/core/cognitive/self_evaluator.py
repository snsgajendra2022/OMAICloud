class SelfEvaluator:


    def evaluate(
        self,
        response
    ):


        checks={

            "empty":
                not bool(response),


            "too_short":
                len(response)<10,


            "valid":
                True

        }


        return checks