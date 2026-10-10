from om_ai.research import ResearchAgent



agent = ResearchAgent()



result = agent.research(

    "Compare Laravel and Django",

    [

        "Laravel is a PHP framework",

        "Django is a Python framework"

    ]

)



print(result)