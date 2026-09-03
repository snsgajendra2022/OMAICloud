"""
OM Workflow Progress Tracker
"""





class WorkflowTracker:



    def update(

        self,

        workflow

    ):


        workflow.update_progress()


        if workflow.progress == 1:


            workflow.status="completed"


        elif workflow.progress > 0:


            workflow.status="running"



        return workflow.to_dict()