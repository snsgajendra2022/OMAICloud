from .training_strategy import TrainingStrategy
from .dataset_selector import DatasetSelector
from .training_scheduler import TrainingScheduler
from .training_manager import TrainingManager
from .training_memory import TrainingMemory
from .training_task import TrainingTask



class TrainingIntelligenceEngine:


    def __init__(self):

        self.strategy = TrainingStrategy()

        self.dataset = DatasetSelector()

        self.scheduler = TrainingScheduler()

        self.manager = TrainingManager()

        self.memory = TrainingMemory()



    def create_training(
        self,
        capability,
        score
    ):


        strategy = (
            self.strategy.decide(
                capability,
                score
            )
        )


        dataset = (
            self.dataset.select(
                capability
            )
        )


        task = TrainingTask(

            capability=capability,

            dataset=dataset["dataset"],

            priority=1-score,

            reason=strategy["strategy"]

        )


        job = (
            self.scheduler.schedule(
                task
            )
        )


        result = (
            self.manager.execute(
                job
            )
        )


        self.memory.add(
            result
        )


        return result