class AgentPermission:



    def __init__(self):

        self.permissions={}



    def allow(
        self,
        agent,
        action
    ):


        self.permissions.setdefault(
            agent,
            []
        ).append(
            action
        )



    def check(
        self,
        agent,
        action
    ):


        return action in self.permissions.get(
            agent,
            []
        )