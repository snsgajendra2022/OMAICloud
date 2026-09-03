"""
OM Self Reflection Generator
"""





class Reflector:



    def reflect(

        self,

        analysis:dict

    ):


        issues=analysis.get(

            "issues",

            []

        )



        improvements=[]



        for issue in issues:


            if issue=="execution_failed":

                improvements.append(

                    "Improve tool execution validation"

                )



            if issue=="low_quality_result":

                improvements.append(

                    "Improve knowledge retrieval and reasoning"

                )



        return {


            "issues":

                issues,


            "improvements":

                improvements

        }