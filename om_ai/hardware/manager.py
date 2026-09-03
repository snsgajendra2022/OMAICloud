"""
OM Hardware Integration Manager
"""


from .gateway import HardwareGateway

from .monitoring import HardwareMonitor





class HardwareManager:



    def __init__(self):


        self.gateway = HardwareGateway()

        self.monitor = HardwareMonitor()



    def execute(

        self,

        device,

        command

    ):


        result=self.gateway.execute(

            device,

            command

        )


        health=self.monitor.check(

            device

        )


        return {


            "execution":

                result,


            "health":

                health

        }