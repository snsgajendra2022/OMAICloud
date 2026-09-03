"""
OM Quality Checker

Evaluates generated results.
"""


from __future__ import annotations




class QualityChecker:



    def evaluate(

        self,

        result:str

    ) -> dict:



        score = 0.0


        issues=[]



        if result:

            score += 0.4


        else:

            issues.append(
                "empty response"
            )



        if len(result) > 100:

            score +=0.2


        else:

            issues.append(
                "response too short"
            )



        if "solution" in result.lower():

            score +=0.2



        if "error" not in result.lower():

            score +=0.2



        return {


            "score":

                round(score,2),


            "approved":

                score >=0.7,


            "issues":

                issues

        }