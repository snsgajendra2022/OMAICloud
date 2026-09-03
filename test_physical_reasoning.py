from om_ai.physical_reasoning import PhysicalReasoningManager



engine = PhysicalReasoningManager()



result = engine.analyze(

    {

        "object":

            {

                "name":

                    "glass"


            },


        "objects":

            [

                "glass",

                "table"

            ],


        "action":

            "push glass"

    }

)



print(result)