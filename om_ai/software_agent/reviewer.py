"""
OM Code Review Intelligence
"""


class CodeReviewer:



    def review(

        self,

        changes

    ):


        issues=[]



        if not changes:

            issues.append(

                "No changes generated"

            )



        return {


            "approved":

                len(issues)==0,


            "issues":

                issues,


            "score":

                1.0

                if not issues

                else 0.5

        }