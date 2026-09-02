from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain


brain = OMCognitiveBrain()


result = brain.process(
    "create Laravel authentication API"
)


print(
    result["agent"]
)


print(
    result["reasoning"].get(
        "agent_execution"
    )
)