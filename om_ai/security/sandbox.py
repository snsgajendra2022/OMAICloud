"""
OM Sandbox Execution Layer

Controls tool execution.
"""





class SandboxRunner:



    def execute(

        self,

        function,

        **kwargs

    ):


        try:


            result=function(

                **kwargs

            )


            return {


                "success":True,


                "result":result

            }




        except Exception as e:


            return {


                "success":False,


                "error":str(e)

            }