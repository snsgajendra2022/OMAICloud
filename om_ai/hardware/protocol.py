"""
OM Hardware Communication Protocol
"""


class HardwareProtocol:



    SUPPORTED = [

        "MQTT",

        "HTTP",

        "SERIAL",

        "GPIO",

        "BLUETOOTH"

    ]



    def validate(

        self,

        protocol

    ):


        return {


            "protocol":

                protocol,


            "supported":

                protocol in self.SUPPORTED

        }