from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain


brain = OMCognitiveBrain()


result = brain.process(
    "Build restaurant management system with database and reports"
)


print("Agent Team:")


print(
    result["reasoning"].get(
        "agent_team"
    )
)