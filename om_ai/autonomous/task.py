"""
OM Autonomous Task Model
"""


from dataclasses import dataclass, field




@dataclass
class Task:


    id: str


    title: str


    description: str


    agent: str = "general"


    status: str = "pending"


    depends_on: list[str] = field(
        default_factory=list
    )


    result: dict = field(
        default_factory=dict
    )



    def complete(
        self,
        result:dict
    ):

        self.status="completed"

        self.result=result



    def to_dict(self):

        return {

            "id":
                self.id,

            "title":
                self.title,

            "description":
                self.description,

            "agent":
                self.agent,

            "status":
                self.status,

            "depends_on":
                self.depends_on,

            "result":
                self.result

        }