"""
OM Device Gateway

Controls communication between
brain and devices.
"""


from .connector import DeviceConnector

from .permission import DevicePermission





class DeviceGateway:



    def __init__(self):


        self.connector = DeviceConnector()

        self.permission = DevicePermission()



    def execute(

        self,

        command

    ):


        check=self.permission.check(

            command

        )



        if not check["allowed"]:


            return {


                "status":

                    "blocked",


                "reason":

                    check["reason"]

            }



        return self.connector.send(

            command

        )