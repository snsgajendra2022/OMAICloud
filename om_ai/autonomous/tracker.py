"""
OM Task Progress Tracker
"""




class ProgressTracker:



    def status(

        self,

        tasks

    ):


        total=len(tasks)


        completed=len(

            [

                t

                for t in tasks

                if t.status=="completed"

            ]

        )



        return {


            "total":

                total,


            "completed":

                completed,


            "progress":

                round(

                    completed /
                    max(total,1),

                    2

                )

        }