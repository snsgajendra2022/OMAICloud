"""
OM Tool Router

Selects best tool.
"""


from .file_tool import FileTool

from .code_tool import CodeTool

from .data_tool import DataTool





class ToolRouter:



    def __init__(self):


        self.tools=[

            FileTool(),

            CodeTool(),

            DataTool()

        ]



    def route(
        self,
        request:str
    ):


        results=[]



        for tool in self.tools:


            score=tool.can_handle(
                request
            )


            results.append(

                {

                    "tool":tool,

                    "name":tool.name,

                    "score":score

                }

            )



        results.sort(

            key=lambda x:x["score"],

            reverse=True

        )


        return results[0]