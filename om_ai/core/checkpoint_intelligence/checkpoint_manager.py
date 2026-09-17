from .benchmark import BenchmarkEngine
from .checkpoint_validator import CheckpointValidator
from .approval_engine import ApprovalEngine



class CheckpointManager:


    def __init__(self):

        self.benchmark=BenchmarkEngine()

        self.validator=CheckpointValidator()

        self.approval=ApprovalEngine()



    def process(
        self,
        checkpoint
    ):


        result = self.benchmark.evaluate(
            checkpoint
        )


        valid = self.validator.validate(
            result
        )


        status = self.approval.approve(
            valid
        )


        checkpoint.status=status


        return checkpoint