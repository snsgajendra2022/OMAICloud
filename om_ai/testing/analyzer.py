"""
OM Code Quality Analyzer
"""



class QualityAnalyzer:



    def analyze(

        self,

        code:str

    ):


        issues=[]



        if len(code) < 50:

            issues.append(

                "Code size too small"

            )



        if "TODO" in code:


            issues.append(

                "Incomplete implementation"

            )



        if "password" in code.lower():

            issues.append(

                "Sensitive keyword detected"

            )



        return {


            "issues":

                issues,


            "quality":

                max(

                    0,

                    1 -

                    len(issues)*0.2

                )

        }