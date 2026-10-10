from om_ai.digital_twin import (

    DigitalEntity,

    DigitalTwinManager

)



entity = DigitalEntity(

    name="Restaurant Kitchen",

    entity_type="facility",

    properties={

        "machines":10,

        "capacity":200

    }

)



manager=DigitalTwinManager()



result=manager.analyze(

    entity,

    {

        "increase_orders":

            20

    }

)



print(result)