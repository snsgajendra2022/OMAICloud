"""
OM Root Cause Analysis
"""



class RootCauseAnalyzer:



    def detect(

        self,

        analysis

    ):


        category = analysis.get(

            "category"

        )



        causes={


            "database":

                "Database configuration or migration issue",


            "security":

                "Permission or authentication issue",


            "code":

                "Implementation error",


            "performance":

                "Resource or optimization issue"

        }



        return causes.get(

            category,

            "Unknown failure cause"

        )