from om_ai.hardware import (

    HardwareDevice,

    HardwareManager

)



device = HardwareDevice(

    name="OM Robot Controller",

    device_type="embedded",

    manufacturer="OM Hardware",

    capabilities=[

        "sensor",

        "motor"

    ]

)



manager = HardwareManager()



result = manager.execute(

    device.name,

    "move_motor"

)



print(result)