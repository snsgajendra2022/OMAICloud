from om_ai.data_engine.continuous import ContinuousLearningPipeline



pipeline = ContinuousLearningPipeline()



dataset=[


    {

        "instruction":
        "Create Laravel API",

        "response":
        "Laravel API with MySQL",

        "quality_score":
        0.95

    },


    {

        "instruction":
        "Create Laravel API",

        "response":
        "Laravel API with MySQL",

        "quality_score":
        0.95

    }


]



result=pipeline.process(
    dataset
)


print(result)