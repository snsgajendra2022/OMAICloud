"""
OM Tool Result Validator
"""





class ToolValidator:



    def validate(

        self,

        result:dict

    ):


        if result.get(

            "success"

        ):


            return {


                "valid":

                    True,


                "status":

                    "completed"

            }



        return {


            "valid":

                False,


            "status":

                "failed",


            "error":

                result.get(
                    "error"
                )

        }