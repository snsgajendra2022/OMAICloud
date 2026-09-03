from om_ai.data_engine.curriculum import (
    DatasetCurriculum,
    TrainingScheduler,
    TrainingPlan
)



dataset=[


{

"instruction":
"print hello python",

"difficulty":
"basic"

},


{

"instruction":
"create REST API",

"difficulty":
"medium"

},


{

"instruction":
"design distributed AI system",

"difficulty":
"advanced"

}

]



curriculum = DatasetCurriculum()



result = curriculum.build(
    dataset
)



print(result)



scheduler = TrainingScheduler()



schedule = scheduler.create_schedule(
    result
)



print(schedule)



plan = TrainingPlan()



print(
    plan.generate(schedule)
)