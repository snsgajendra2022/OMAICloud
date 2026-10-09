from om_ai.cognition.task_planner import TaskPlanner


planner = TaskPlanner()


tests = [

    "create react native login and dashboard app",

    "build laravel api with mysql",

    "create AI chatbot system",

    "create react admin dashboard"

]


for item in tests:

    print("\nQUESTION:")
    print(item)

    result = planner.decompose(item)

    print("\nPLAN:")
    print(result)