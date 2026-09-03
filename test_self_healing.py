from om_ai.recovery import SelfHealingEngine



engine = SelfHealingEngine()



result = engine.recover(

    "Create database migration",

    "SQL connection timeout",

    "database"

)



print(result)