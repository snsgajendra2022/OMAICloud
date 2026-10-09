from om_ai.workflow_memory import (
    WorkflowLearningEngine,
    StrategyMatcher
)



engine = WorkflowLearningEngine()



result = engine.learn(

    {

        "goal":

        "Build restaurant management SaaS",


        "tasks":[

            {

                "title":

                "Database Design"

            },

            {

                "title":

                "Backend API"

            },

            {

                "title":

                "Frontend Development"

            }

        ]

    },

    success=True,

    score=0.92

)



print(result)



matcher = StrategyMatcher()



print(

matcher.match(

    "Build hotel management SaaS",

    engine.all()

)

)