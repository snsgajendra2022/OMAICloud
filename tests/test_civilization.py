from om_ai.core.civilization import CivilizationEngine


om = CivilizationEngine()


mission = om.create_mission(
    "Create ecommerce software application"
)


print(
    mission
)


print(
    om.assign_tasks(
        mission
    )
)