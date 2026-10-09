from om_ai.tools.security import ToolSafetyManager



security = ToolSafetyManager()



tests=[

    "read python file",

    "delete system files",

    "drop database"

]



for item in tests:


    result = security.check(

        "file",

        item

    )


    print(
        item
    )


    print(
        result
    )