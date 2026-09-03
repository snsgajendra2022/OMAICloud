"""
Code Analysis Tool
"""


from .base import BaseTool




class CodeTool(BaseTool):


    name="code"



    def can_handle(
        self,
        request
    ):


        keywords=[

            "debug",

            "error",

            "bug",

            "code",

            "function",

            "class"

        ]


        return 0.8 if any(

            x in request.lower()

            for x in keywords

        ) else 0.0



    def execute(
        self,
        request,
        context=None
    ):


        return {


            "tool":"code",

            "operation":

            "analysis"

        }