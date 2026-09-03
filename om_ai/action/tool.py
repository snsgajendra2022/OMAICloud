"""
OM Autonomous Tool Model
"""


from dataclasses import dataclass
from typing import Callable, Any



@dataclass
class Tool:


    name: str


    description: str


    function: Callable


    def execute(

        self,

        **kwargs

    ) -> Any:


        return self.function(

            **kwargs

        )