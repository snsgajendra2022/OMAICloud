"""
OM Test Case Model
"""


from dataclasses import dataclass, field



@dataclass
class TestCase:


    name:str


    description:str


    category:str = "functional"


    expected:str = ""


    status:str = "pending"



    def to_dict(self):

        return {


            "name":
                self.name,


            "description":
                self.description,


            "category":
                self.category,


            "expected":
                self.expected,


            "status":
                self.status

        }