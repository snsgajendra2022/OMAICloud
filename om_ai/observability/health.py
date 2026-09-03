"""
OM Health Monitor
"""





class HealthMonitor:



    def check(

        self,

        metrics:dict

    ):


        failures = metrics.get(

            "counters",

            {}

        ).get(

            "errors",

            0

        )



        if failures > 10:


            return {


                "status":

                    "warning",


                "reason":

                    "high error rate"

            }



        return {


            "status":

                "healthy",


            "reason":

                "normal operation"

        }