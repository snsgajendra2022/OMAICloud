class RequirementAnalyzer:


    def analyze(
        self,
        message
    ):


        text=message.lower()


        result={

            "framework":[],

            "features":[]

        }


        for tech in [
            "react",
            "python",
            "laravel",
            "flutter"
        ]:

            if tech in text:

                result["framework"].append(
                    tech
                )


        if "login" in text:

            result["features"].append(
                "authentication"
            )


        if "dashboard" in text:

            result["features"].append(
                "dashboard"
            )


        return result