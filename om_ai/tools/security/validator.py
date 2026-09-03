"""
OM Tool Risk Validator
"""


import re




class ToolValidator:



    BLOCKED_PATTERNS=[


        r"rm\s+-rf",

        r"delete\s+system",

        r"format\s+disk",

        r"drop\s+database",

        r"shutdown"

    ]



    def validate(
        self,
        request:str
    ) -> dict:



        for pattern in self.BLOCKED_PATTERNS:


            if re.search(
                pattern,
                request,
                re.I
            ):


                return {


                    "safe":

                        False,


                    "reason":

                        "dangerous operation detected"

                }



        return {


            "safe":

                True,


            "reason":

                "request validated"

        }