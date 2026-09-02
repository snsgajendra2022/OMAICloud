from om_ai.core.reasoning.pipeline import run_reasoning_pipeline


result = run_reasoning_pipeline(
    "create react native login and dashboard app"
)


print(result["technology"])

print("\nKnowledge:")
print(result["knowledge"])

print("\nAnswer:")
print(result["markdown"])