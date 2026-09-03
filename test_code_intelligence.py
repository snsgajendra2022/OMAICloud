from om_ai.code_intelligence import CodeUnderstandingEngine



engine = CodeUnderstandingEngine()



result = engine.analyze(

    "."

)



print(

    "Files:",

    len(result["files"])

)


print(

    result["architecture"]

)