from om_ai.goals import GoalManager



manager = GoalManager()



goal = manager.create_goal(

    "Restaurant Management SaaS",

    "Build complete restaurant platform",

    [

        {

            "id":"1",

            "title":"Database Design",

            "status":"completed"

        },

        {

            "id":"2",

            "title":"Backend API",

            "status":"pending"

        }

    ]

)



print(goal)