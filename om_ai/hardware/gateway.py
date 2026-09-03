"""
OM Hardware Gateway

Central communication layer.
"""


from .driver import DeviceDriver

from .controller import EmbeddedController





class HardwareGateway:



    def __init__(self):


        self.driver = DeviceDriver()

        self.controller = EmbeddedController()



    def execute(

        self,

        device,

        command

    ):


        connection=self.driver.connect(

            device

        )


        result=self.controller.control(

            command

        )


        return {


            "connection":

                connection,


            "result":

                result

        }