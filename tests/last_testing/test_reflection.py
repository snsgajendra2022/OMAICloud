from om_ai.reflection import ReflectionEngine



engine = ReflectionEngine()



result = engine.process(

    {

        "success":False,

        "error":

        "tool failed"

    },

    {

        "approved":False,

        "score":0.3

    }

)



print(result)