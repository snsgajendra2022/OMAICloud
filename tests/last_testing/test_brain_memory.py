from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain


brain = OMCognitiveBrain()


first = brain.process(
    "I am building OM AI using Python"
)


second = brain.process(
    "continue my project"
)


print(second["answer"])