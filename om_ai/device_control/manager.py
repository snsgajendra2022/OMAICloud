"""
OM Device Control Manager
"""


from .gateway import DeviceGateway

from .feedback import DeviceFeedback

from .memory import DeviceMemory





class DeviceControlManager:



    def __init__(self):


        self.gateway = DeviceGateway()

        self.feedback = DeviceFeedback()

        self.memory = DeviceMemory()



    def execute(

        self,

        command

    ):


        response=self.gateway.execute(

            command

        )


        result=self.feedback.process(

            response

        )


        self.memory.store(

            result

        )


        return result