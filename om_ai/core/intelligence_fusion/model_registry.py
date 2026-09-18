from dataclasses import dataclass, field


@dataclass
class IntelligenceModel:

    name: str

    provider: str

    capabilities: list[str] = field(
        default_factory=list
    )

    local: bool = True

    performance: dict = field(
        default_factory=dict
    )

    available: bool = True



class ModelRegistry:


    def __init__(self):

        self.models = {}



    def register(
        self,
        model: IntelligenceModel
    ):

        self.models[
            model.name
        ] = model



    def remove(
        self,
        name:str
    ):

        self.models.pop(
            name,
            None
        )



    def get(
        self,
        name:str
    ):

        return self.models.get(
            name
        )



    def all(self):

        return list(
            self.models.values()
        )



    def available_models(self):

        return [

            m for m in self.models.values()

            if m.available

        ]