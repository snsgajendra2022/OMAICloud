"""
OM Software Change Planner
"""


class ChangePlanner:



    def plan(

        self,

        requirement,

        repository_context

    ):


        plan=[]



        text=requirement.lower()



        if "login" in text:


            plan.extend([

                "Find authentication files",

                "Analyze user model",

                "Update login flow",

                "Add validation",

                "Create tests"

            ])



        elif "api" in text:


            plan.extend([

                "Find API routes",

                "Analyze controllers",

                "Update service layer",

                "Validate responses"

            ])



        else:


            plan.extend([

                "Analyze requirement",

                "Locate affected files",

                "Implement change",

                "Run validation"

            ])



        return plan