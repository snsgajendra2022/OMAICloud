


from om_ai.evaluation.knowledge_confidence import KnowledgeConfidenceEngine


engine = KnowledgeConfidenceEngine()


result = engine.evaluate(

    "what is git",

    [
        {
            "text":"Git is distributed version control system",
            "score":0.92
        }
    ]

)


print(result)