from om_ai.universal_robotics import UniversalRoboticsManager



robot = UniversalRoboticsManager()



result = robot.execute(

    "pick object and place on table",

    {

        "objects":[

            "cup",

            "table"

        ]

    }

)



print(result)