"""
OM Tool Selection Planner
"""





class ToolPlanner:



    def select(

        self,

        task:str

    ):


        task=task.lower()



        tools=[]



        if any(

            x in task

            for x in [

                "create file",

                "write",

                "generate code"

            ]

        ):

            tools.append(

                "file_writer"

            )



        if any(

            x in task

            for x in [

                "run",

                "execute",

                "test"

            ]

        ):

            tools.append(

                "code_executor"

            )



        if any(

            x in task

            for x in [

                "database",

                "sql",

                "query"

            ]

        ):

            tools.append(

                "database"

            )



        return tools