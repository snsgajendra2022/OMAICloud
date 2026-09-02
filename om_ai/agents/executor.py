"""
OM Agent Execution Engine

Runs selected agent behavior.
"""


from __future__ import annotations

from typing import Any





class AgentExecutor:



    def execute(
        self,
        agent_result: dict[str, Any],
        question: str,
        context: dict | None = None
    ) -> dict[str, Any]:


        context = context or {}


        agent = agent_result.get(
            "agent"
        )


        name = agent_result.get(
            "name",
            "general"
        )


        if not agent:

            return {

                "agent":"general",

                "mode":"default"

            }



        result = agent.execute(

            question,

            context

        )


        return {


            "agent":

                name,


            "score":

                agent_result.get(
                    "score",
                    0
                ),


            "execution":

                result


        }