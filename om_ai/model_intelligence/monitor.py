"""
OM Model Runtime Monitoring
"""


class ModelMonitor:



    def collect(

        self,

        request,

        response,

        score=None

    ):


        return {


            "request":

                request,


            "response":

                response,


            "quality":

                score,


            "feedback":

                "stored"

        }