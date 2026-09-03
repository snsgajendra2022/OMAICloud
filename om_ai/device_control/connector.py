"""
OM Hardware Connector Layer

Future integrations:

- MQTT
- REST APIs
- GPIO
- Arduino
- Raspberry Pi
"""


class DeviceConnector:



    def send(

        self,

        command

    ):


        return {


            "device":

                command.device,


            "action":

                command.action,


            "status":

                "sent"

        }