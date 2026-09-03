"""
OM Failure Analysis Engine
"""


class ReflectionAnalyzer:


    def analyze(

        self,

        execution:dict,

        evaluation:dict | None = None

    ):


        issues=[]


        if not execution.get("success", True):

            issues.append(

                "execution_failed"

            )


        if evaluation:


            score=evaluation.get(

                "score",

                1

            )


            if score < 0.5:

                issues.append(

                    "low_quality_result"

                )


        return {


            "issues":

                issues,


            "severity":

                "high"

                if issues

                else

                "normal"

        }