from om_ai.action import (
    ToolExecutor,
    ToolPlanner,
    ToolValidator,
    register_builtin_tools
)



executor = ToolExecutor()


register_builtin_tools(
    executor
)



planner = ToolPlanner()



tools = planner.select(

    "create file with python code"

)



print(

    tools

)



result = executor.execute(

    "file_writer",

    path="data/test/demo.txt",

    content="OM created this file"

)



print(result)



validator = ToolValidator()


print(

    validator.validate(result)

)