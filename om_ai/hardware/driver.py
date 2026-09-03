"""
OM Hardware Driver System
"""


class DeviceDriver:



    def connect(

        self,

        device

    ):


        return {


            "device":

                device,


            "status":

                "connected"

        }



    def send(

        self,

        command

    ):


        return {


            "command":

                command,


            "status":

                "executed"

        }