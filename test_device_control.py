from om_ai.device_control import (

    DeviceCommand,

    DeviceControlManager

)



manager = DeviceControlManager()



command = DeviceCommand(

    device="office_light",

    action="turn_on",

    parameters={}

)



result = manager.execute(

    command

)



print(result)