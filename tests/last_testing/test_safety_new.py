from om_ai.safety import SafetyManager



safety=SafetyManager()



result=safety.validate(

    "create restaurant report"

)



print(result)



danger=safety.validate(

    "delete database"

)



print(danger)