"""
OM Performance Analyzer
"""





class PerformanceAnalyzer:



    def analyze(

        self,

        metrics,

        events

    ):



        counters = metrics.get(

            "counters",

            {}

        )



        return {


            "executions":

                counters.get(

                    "executions",

                    0

                ),


            "errors":

                counters.get(

                    "errors",

                    0

                ),


            "success_rate":

                self._success_rate(

                    counters

                )

        }




    def _success_rate(

        self,

        counters

    ):


        total=counters.get(

            "executions",

            0

        )


        errors=counters.get(

            "errors",

            0

        )


        if total==0:

            return 0



        return round(

            (total-errors)/total,

            3

        )