"""
OM Device Feedback Intelligence
"""


class DeviceFeedback:



    def process(

        self,

        response

    ):


        return {


            "success":

                response.get(

                    "status"

                ) == "sent",


            "response":

                response

        }