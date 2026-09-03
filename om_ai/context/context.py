"""
OM Context Model
"""


from dataclasses import dataclass, field



@dataclass
class Context:


    user:dict = field(
        default_factory=dict
    )


    project:dict = field(
        default_factory=dict
    )


    environment:dict = field(
        default_factory=dict
    )


    task:str = ""


    history:list = field(
        default_factory=list
    )



    def to_dict(self):

        return {

            "user": self.user,

            "project": self.project,

            "environment": self.environment,

            "task": self.task,

            "history": self.history

        }