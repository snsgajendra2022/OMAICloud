from .input_gateway import InputGateway
from om_ai.perception.document.pdf.manager import PDFManager

class PerceptionManager:


    def __init__(self):

        self.gateway = InputGateway()
        self.pdf = PDFManager()


    def process(self, data):

        input_data = self.gateway.receive(data)
        if input_data.input_type == "pdf":

            return self.pdf.process(
                input_data.content
            )

        return {

            "type":
                input_data.input_type,


            "status":
                "received",

            "message":
                "Input ready for processing"

        }