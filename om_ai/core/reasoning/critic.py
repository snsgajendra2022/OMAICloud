class Critic:


    def review(self, answer):


        issues=[]


        if len(answer)<20:

            issues.append(
                "Response too short"
            )


        return {

            "approved":
                len(issues)==0,

            "issues":
                issues

        }