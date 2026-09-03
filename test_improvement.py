from om_ai.improvement import KnowledgeImprovementEngine

engine = KnowledgeImprovementEngine()



result = engine.improve(

    "Create Laravel restaurant API",

    "Laravel API architecture with MySQL database",

    {

        "approved":True,

        "score":0.95

    }

)



print(result)