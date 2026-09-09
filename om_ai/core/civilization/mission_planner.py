class MissionPlanner:


    def create(
        self,
        goal
    ):


        tasks=[]


        text=goal.lower()


        if "software" in text or "app" in text:

            tasks.extend([

                "Analyze requirements",

                "Design architecture",

                "Implement code",

                "Test system"

            ])


        else:

            tasks.append(
                "Analyze objective"
            )


        return tasks