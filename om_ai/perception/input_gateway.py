from .input_detector import InputDetector
from .models import PerceptionInput


class InputGateway:


    def __init__(self):

        self.detector = InputDetector()



    def receive(
        self,
        data,
        metadata=None
    ):


        input_type = self.detector.detect(data)


        return PerceptionInput(

            input_type=input_type,

            content=data,

            metadata=metadata

        )