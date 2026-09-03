"""
OM Failure Analysis Engine
"""



class FailureAnalyzer:



    def analyze(

        self,

        failure:dict

    ):


        error = str(

            failure.get(

                "error",

                ""

            )

        ).lower()



        category = "unknown"



        if "database" in error or "sql" in error:

            category = "database"



        elif "permission" in error:

            category = "security"



        elif "syntax" in error:

            category = "code"



        elif "timeout" in error:

            category = "performance"



        return {


            "category":

                category,


            "severity":

                failure.get(

                    "severity",

                    "medium"

                ),


            "needs_retry":

                True

        }