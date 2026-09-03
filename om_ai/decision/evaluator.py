"""
OM Decision Evaluation Engine
"""




class DecisionEvaluator:



    def score(

        self,

        option

    ):


        score = (

            option.performance_score * 0.4

            +

            option.cost_score * 0.2

            +

            (1 - option.complexity_score) * 0.2

            +

            len(option.benefits) * 0.05

            -

            len(option.risks) * 0.05

        )



        return round(

            max(0, min(score,1)),

            3

        )