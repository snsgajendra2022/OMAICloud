"""
OM Workflow Failure Recovery
"""





class WorkflowRecovery:



    def recover(

        self,

        task,

        error

    ):


        return {


            "task":

                task,


            "error":

                error,


            "action":

                "retry_with_alternative_strategy"

        }