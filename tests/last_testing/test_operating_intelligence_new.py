from om_ai.operating_intelligence import OMOperatingManager



class TestModule:


    def process(

        self,

        task

    ):


        return {


            "completed":

                True,


            "task":

                task

        }





om = OMOperatingManager()



om.register_module(

    "test",

    TestModule()

)



result = om.run(

    "analyze restaurant system"

)



print(result)



print(

    om.status()

)