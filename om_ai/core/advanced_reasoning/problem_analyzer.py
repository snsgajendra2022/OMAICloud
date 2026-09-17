class ProblemAnalyzer:



    def analyze(
        self,
        problem
    ):


        return {


            "complexity":

                min(
                    len(problem.split())/100,
                    1
                ),


            "requires_steps":

                len(problem.split())>10

        }