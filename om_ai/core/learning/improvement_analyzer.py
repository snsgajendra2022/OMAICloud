class ImprovementAnalyzer:


    def analyze(
        self,
        evaluation
    ):


        if evaluation["quality"]=="poor":

            return {

                "improvement_required":
                    True

            }


        return {

            "improvement_required":
                False

        }