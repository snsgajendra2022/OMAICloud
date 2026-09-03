"""
File Management Tool

Safe file operations.
"""


from pathlib import Path

from .base import BaseTool




class FileTool(BaseTool):


    name="file"



    def can_handle(
        self,
        request:str
    ) -> float:


        keywords=[

            "file",

            "folder",

            "read",

            "write",

            "create",

            "open"

        ]


        score=0


        for word in keywords:

            if word in request.lower():

                score +=0.15


        return min(
            score,
            1
        )



    def execute(
        self,
        request,
        context=None
    ):


        return {


            "tool":

                self.name,


            "action":

                "file_operation",


            "status":

                "ready"

        }