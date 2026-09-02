


from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain


brain = OMCognitiveBrain()


result = brain.process(
    "tell me about my restaurant project"
)


print(result["answer"])

print("\nMEMORY")

print(
    result["debug"]
)