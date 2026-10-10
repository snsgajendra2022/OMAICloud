from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain


brain = OMCognitiveBrain()


result = brain.process(
    "create react native login and dashboard app"
)


print("\nANSWER")
print(result["answer"])


print("\nEVALUATION")
print(result["evaluation"])


print("\nTECHNOLOGY")
print(result["technology"])


print("\nTASKS")
print(result["tasks"])