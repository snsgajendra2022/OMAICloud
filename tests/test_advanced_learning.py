from om_ai.core.advanced_learning import (
    AdvancedLearningEngine,
    LearningRecord
)


engine = AdvancedLearningEngine()


records=[

LearningRecord(
    "create react dashboard",
    "React dashboard created"
),

LearningRecord(
    "create react login",
    "React login created"
)

]


result = engine.learn(records)


print(result)