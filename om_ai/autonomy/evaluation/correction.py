"""
OM Correction Planner

Creates improvement actions.
"""




class CorrectionPlanner:



    def create(

        self,

        evaluation:dict

    ) -> list[str]:


        actions=[]



        for issue in evaluation.get(
            "issues",
            []
        ):


            if "empty" in issue:

                actions.append(
                    "Generate complete response"
                )


            if "short" in issue:

                actions.append(
                    "Add more explanation"
                )



        if not actions:

            actions.append(
                "Improve reasoning quality"
            )



        return actions