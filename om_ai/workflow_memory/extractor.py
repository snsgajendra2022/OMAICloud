"""
OM Workflow Pattern Extractor
"""



class WorkflowExtractor:



    def extract(

        self,

        workflow:dict

    ):


        tasks = workflow.get(

            "tasks",

            []

        )


        pattern=[]



        for task in tasks:


            pattern.append(

                task.get(

                    "title"

                )

            )


        return {


            "pattern":

                pattern,


            "task_count":

                len(pattern)

        }