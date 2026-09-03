from om_ai.autonomous import AutonomousPlanner



planner = AutonomousPlanner()



tasks = planner.create_plan(

    "Build restaurant management system"

)



for task in tasks:

    print(
        task.to_dict()
    )