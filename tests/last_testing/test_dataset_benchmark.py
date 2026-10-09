from om_ai.data_engine.benchmark import (
    DatasetBenchmark,
    BenchmarkReport
)



dataset=[


{

"instruction":
"Create Laravel API",

"response":
"Create Laravel backend API with authentication and MySQL database",

"category":
"engineering"

},


{

"instruction":
"",

"response":
""

}

]



benchmark = DatasetBenchmark()



result = benchmark.run(
    dataset
)


print(result)



report = BenchmarkReport()



print(
    report.generate(result)
)