class TrainingStrategy:


    def decide(
        self,
        capability,
        score
    ):


        if score < 0.5:

            return {

                "strategy":
                    "intensive_training",

                "epochs":
                    5

            }


        if score < 0.75:

            return {

                "strategy":
                    "targeted_training",

                "epochs":
                    2

            }



        return {

            "strategy":
                "maintenance",

            "epochs":
                1

        }