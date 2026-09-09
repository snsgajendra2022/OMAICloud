
from om_ai.core.agents import CodingAgent, QualityAgent
from om_ai.core.agents.collaboration_engine import CollaborationEngine


engine = CollaborationEngine()


engine.register_agent(
    CodingAgent()
)

engine.register_agent(
    QualityAgent()
)


result = engine.execute(

    "create react dashboard",

    {
        "intent":
        "coding"
    },

    {
        "plan":
        [
            "analyze",
            "build"
        ]
    }

)


print(result)