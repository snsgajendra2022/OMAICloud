from om_ai.learning import LearningEngine


engine = LearningEngine()


result = engine.learn(

    "Build restaurant management system",

    "Created Laravel architecture",

    {
        "approved": True,
        "score": 0.9
    }

)


print(result)