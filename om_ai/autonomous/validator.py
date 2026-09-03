"""
OM Autonomous Result Validator
"""




class ResultValidator:



    def validate(

        self,

        tasks

    ):


        failed=[

            t.id

            for t in tasks

            if t.status!="completed"

        ]



        return {


            "success":

                len(failed)==0,


            "failed_tasks":

                failed

        }