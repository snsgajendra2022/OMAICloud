"""
OM Agent Execution Engine

Runs selected agent behavior.

Flow:

Agent Router
      |
      ↓
Agent Executor
      |
      ├── Tool Router
      |
      ├── Tool Execution
      |
      └── Agent Execution

"""


from __future__ import annotations


from typing import Any


from om_ai.tools import ToolRouter
from om_ai.tools.security import ToolSafetyManager




class AgentExecutor:



    def __init__(self):


        self.tool_router = ToolRouter()
        self.safety = ToolSafetyManager()




    def execute(

        self,

        agent_result: dict[str, Any],

        question: str,

        context: dict | None = None

    ) -> dict[str, Any]:



        context = context or {}



        # ----------------------------
        # Selected Agent
        # ----------------------------


        agent = agent_result.get(
            "agent"
        )


        name = agent_result.get(
            "name",
            "general"
        )



        if not agent:


            return {


                "agent":
                    "general",


                "score":
                    0,


                "execution": {


                    "mode":
                        "default"


                }


            }



        # ----------------------------
        # Tool Selection
        # ----------------------------


        tool_result = self.tool_router.route(
            question
        )



        tool_execution = None



        if tool_result and tool_result.get("tool"):


            tool = tool_result["tool"]


            try:


                tool_execution = tool.execute(

                    question,

                    context

                )

                safety_result = self.safety.check(

                    tool_result.get("name"),

                    question

                )
                if safety_result["approved"]:
                    tool_execution = tool.execute(
                        question,
                        context
                    )

                else:
                        tool_execution = {
                            "blocked":
                                True,
                            "reason":
                                safety_result["reason"]

                        }
            except Exception as error:


                tool_execution = {


                    "tool":

                        tool_result.get(
                            "name"
                        ),


                    "error":

                        str(error)


                }



        # ----------------------------
        # Agent Context
        # ----------------------------


        agent_context = {


            **context,


            "tool":

                tool_result,


            "tool_result":

                tool_execution

        }



        # ----------------------------
        # Execute Agent
        # ----------------------------


        result = agent.execute(

            question,

            agent_context

        )



        # ----------------------------
        # Final Execution Result
        # ----------------------------


        return {


            "agent":

                name,


            "score":

                agent_result.get(
                    "score",
                    0
                ),



            "tool":

                {


                    "name":

                        tool_result.get(
                            "name"
                        )
                        if tool_result

                        else None,


                    "score":

                        tool_result.get(
                            "score"
                        )
                        if tool_result

                        else 0,


                },



            "tool_execution":

                tool_execution,



            "execution":

                result


        }