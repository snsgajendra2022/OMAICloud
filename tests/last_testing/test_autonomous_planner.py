from om_ai.autonomy import (
    AutonomousPlanner,
    AutonomousExecutor
)



planner = AutonomousPlanner()



goal = planner.create_plan(

    "Build restaurant management system"

)



print(
    goal.description
)


print(
    goal.tasks
)



executor = AutonomousExecutor()


executor.load(
    goal.tasks
)


while True:


    result = executor.execute_next()


    print(result)


    if result["status"]=="completed":

        break