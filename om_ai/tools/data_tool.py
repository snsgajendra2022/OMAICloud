"""
Data Processing Tool
"""


from .base import BaseTool




class DataTool(BaseTool):


    name="data"



    def can_handle(
        self,
        request
    ):


        return 0.8 if any(

            x in request.lower()

            for x in [

                "csv",

                "excel",

                "report",

                "chart",

                "data"

            ]

        ) else 0.0



    def execute(
        self,
        request,
        context=None
    ):


        return {


            "tool":"data",

            "operation":

            "data_processing"

        }