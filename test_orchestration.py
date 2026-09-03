from om_ai.orchestration import OMOrchestrator



engine = OMOrchestrator()



result = engine.orchestrate(

    "Create Laravel restaurant system",

    {

        "name":

        "coding"

    },

    memory={

        "project":

        "restaurant"

    },

    knowledge=[

        "Laravel API"

    ]

)



print(result)