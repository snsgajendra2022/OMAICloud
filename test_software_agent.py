from om_ai.software_agent import SoftwareEngineeringAgent



agent = SoftwareEngineeringAgent()



result = agent.analyze_project(

    ".",

    "Add login authentication API"

)



print(result["plan"])


print(result["review"])