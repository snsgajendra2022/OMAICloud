class AgentMemory:


    def __init__(self):

        self.storage={}



    def remember(
        self,
        agent,
        data
    ):


        if agent not in self.storage:

            self.storage[agent]=[]


        self.storage[agent].append(
            data
        )



    def recall(
        self,
        agent
    ):

        return self.storage.get(
            agent,
            []
        )