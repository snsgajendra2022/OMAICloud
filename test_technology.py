from om_ai.cognition.technology_engine import TechnologyEngine


engine = TechnologyEngine()


tests = [

    "create react native login screen",

    "create react dashboard",

    "build laravel api with mysql",

    "create fastapi backend",

    "make docker deployment",

    "build flutter mobile app"

]


for item in tests:

    print("\nQUESTION:")
    print(item)

    result = engine.analyze(item)

    print(result)