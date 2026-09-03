"""
OM Workflow Strategy Model
"""


from dataclasses import dataclass



@dataclass
class WorkflowStrategy:


    name:str


    pattern:list


    confidence:float = 0.0



    def to_dict(self):

        return {

            "name":
                self.name,

            "pattern":
                self.pattern,

            "confidence":
                self.confidence

        }