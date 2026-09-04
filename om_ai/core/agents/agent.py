class Agent:


    def __init__(
        self,
        name,
        role
    ):

        self.name = name

        self.role = role

        self.memory = []



    def receive(
        self,
        task
    ):

        return {

            "agent":
                self.name,

            "task":
                task

        }



    def execute(
        self,
        task
    ):

        return {

            "status":
                "completed",

            "result":
                f"{self.name} executed {task}"

        }