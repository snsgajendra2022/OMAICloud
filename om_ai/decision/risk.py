"""
OM Risk Analysis Engine
"""




class RiskAnalyzer:



    def analyze(

        self,

        option

    ):


        risks=[]



        if option.complexity_score > 0.7:

            risks.append(

                "high complexity"

            )



        if len(option.risks)>2:

            risks.append(

                "multiple risk factors"

            )



        return {


            "risks":

                risks,


            "level":

                "high"

                if risks

                else

                "low"

        }