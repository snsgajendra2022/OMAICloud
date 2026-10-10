from om_ai.cognition.intent_engine import IntentEngine


engine = IntentEngine()


tests = [
    "create react fastapi dashboard",
    "what is pm in india",
    "fix laravel api error"
]


for question in tests:

    result = engine.analyze(question)

    print("\nQuestion:")
    print(question)

    print("Intent:")
    print(result)