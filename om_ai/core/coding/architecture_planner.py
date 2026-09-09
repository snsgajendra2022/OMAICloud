class ArchitecturePlanner:


    def create(
        self,
        requirement
    ):


        return {

            "frontend":
                requirement["framework"],

            "features":
                requirement["features"],

            "security":[
                "validation",
                "authentication"
            ]

        }