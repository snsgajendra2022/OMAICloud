"""
OM Model Intelligence Manager
"""


from .registry import ModelRegistry

from .adapter import ModelAdapter

from .finetune import FineTuneManager

from .evaluator import ModelEvaluator

from .deployment import ModelDeployment

from .monitor import ModelMonitor





class ModelIntelligenceManager:



    def __init__(self):


        self.registry = ModelRegistry()

        self.adapter = ModelAdapter()

        self.finetune = FineTuneManager()

        self.evaluator = ModelEvaluator()

        self.deploy = ModelDeployment()

        self.monitor = ModelMonitor()



    def create_model(

        self,

        model

    ):


        self.registry.register(

            model

        )


        return {


            "created":

                True,


            "model":

                model

        }