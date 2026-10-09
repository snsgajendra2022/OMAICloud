


from om_ai.data_engine.intelligence.engine import TrainingDataIntelligence


engine = TrainingDataIntelligence()



dataset=[


{

"instruction":

"Create Laravel API with MySQL database",


"response":

"Build production backend architecture"

}

]



result=engine.analyze(
    dataset
)



print(result)