from om_ai.data_engine.improvement import DatasetImprovementAgent



agent = DatasetImprovementAgent()



dataset=[


{

"instruction":

"Create API",


"response":

"ok"

},


{

"instruction":

"Build Laravel system",


"response":

"Complete Laravel backend with authentication, database design and API implementation"

}

]



result = agent.improve(
    dataset
)


print(result)