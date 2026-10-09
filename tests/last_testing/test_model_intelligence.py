from om_ai.model_intelligence import (

    OMModel,

    ModelIntelligenceManager

)



model = OMModel(

    name="OM-Foundation",

    version="0.1",

    model_type="LLM",

    parameters="7B",

    capabilities=[

        "reasoning",

        "coding",

        "research"

    ]

)



manager = ModelIntelligenceManager()



print(

    manager.create_model(

        model.to_dict()

    )

)