from datetime import datetime



class TrainingScheduler:



    def __init__(self):

        self.jobs=[]



    def schedule(
        self,
        task
    ):


        job={

            "task":task,

            "created":

                datetime.utcnow()
                .isoformat(),

            "status":

                "queued"

        }


        self.jobs.append(
            job
        )


        return job