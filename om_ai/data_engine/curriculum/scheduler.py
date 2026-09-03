"""
OM Training Scheduler

Creates training order.
"""





class TrainingScheduler:



    ORDER = [

        "basic",

        "medium",

        "advanced"

    ]



    def create_schedule(

        self,

        curriculum:dict

    ):


        schedule=[]



        batch=1



        for level in self.ORDER:


            items = curriculum.get(

                level,

                []

            )


            if items:


                schedule.append(

                    {

                        "batch":

                            batch,


                        "level":

                            level,


                        "samples":

                            len(items)

                    }

                )


                batch += 1



        return schedule