"""
OM Agent Capability Registry
"""


from .capability import AgentCapability





class AgentRegistry:



    def __init__(self):


        self.agents = [

            AgentCapability(

                name="coding",

                skills=[

                    "code",

                    "development",

                    "api",

                    "frontend",

                    "backend"

                ],

                domains=[

                    "software",

                    "application"

                ]

            ),


            AgentCapability(

                name="database",

                skills=[

                    "database",

                    "schema",

                    "sql",

                    "migration"

                ],

                domains=[

                    "data"

                ]

            ),


            AgentCapability(

                name="research",

                skills=[

                    "research",

                    "documentation",

                    "analysis"

                ],

                domains=[

                    "knowledge"

                ]

            ),


            AgentCapability(

                name="testing",

                skills=[

                    "test",

                    "validation",

                    "quality"

                ],

                domains=[

                    "software"

                ]

            ),


            AgentCapability(

                name="security",

                skills=[

                    "security",

                    "authentication",

                    "permission"

                ],

                domains=[

                    "security"

                ]

            )

        ]



    def available(self):

        return self.agents