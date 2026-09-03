from om_ai.workflow import (
    WorkflowGenerator,
    WorkflowPlanner,
    Workflow,
    WorkflowExecutor
)



generator = WorkflowGenerator()


tasks = generator.generate(

    "Build complete restaurant management application"

)



planner = WorkflowPlanner()


tasks = planner.plan(

    tasks

)



workflow = Workflow(

    id="workflow001",

    goal=
    "Build complete restaurant management application",

    tasks=tasks

)



executor = WorkflowExecutor()



result = executor.execute(

    workflow

)



print(result)