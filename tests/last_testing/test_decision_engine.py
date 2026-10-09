from om_ai.decision import (
    DecisionEngine,
    DecisionOption
)



engine = DecisionEngine()



options=[


DecisionOption(

    name="Laravel",

    description="PHP framework",

    benefits=[

        "fast development",

        "large ecosystem"

    ],

    risks=[

        "PHP dependency"

    ],

    cost_score=0.8,

    performance_score=0.8,

    complexity_score=0.3

),



DecisionOption(

    name="Node",

    description="Javascript backend",

    benefits=[

        "real time"

    ],

    risks=[

        "scaling complexity"

    ],

    cost_score=0.7,

    performance_score=0.7,

    complexity_score=0.5

)

]



result=engine.decide(

    "Build restaurant management system",

    options

)



print(result)