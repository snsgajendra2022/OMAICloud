from om_ai.collaboration import AgentCoordinator




coordinator = AgentCoordinator()



result = coordinator.collaborate(

    {

        "id":"task_1",

        "description":

        "Design restaurant database"

    },


    [

        "database",

        "coding",

        "testing"

    ]

)



print(result)