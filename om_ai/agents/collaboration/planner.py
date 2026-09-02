"""
OM Multi Agent Planner

Decides which agents should work together.
"""


from __future__ import annotations

import re




class AgentCollaborationPlanner:



    def plan(
        self,
        question:str
    ) -> list[str]:


        agents=[]


        q = question.lower()



        # Coding

        if re.search(
            r"\b(build|create|develop|code|app|software|api|system)\b",
            q
        ):

            agents.append(
                "coding"
            )



        # Database

        if re.search(
            r"\b(database|mysql|sql|schema|migration|data)\b",
            q
        ):

            agents.append(
                "database"
            )



        # Business

        if re.search(
            r"\b(business|restaurant|finance|sales|report|management)\b",
            q
        ):

            agents.append(
                "business"
            )



        # Research

        if re.search(
            r"\b(research|analysis|study|compare)\b",
            q
        ):

            agents.append(
                "research"
            )



        # Always include memory

        agents.append(
            "memory"
        )



        return list(
            dict.fromkeys(
                agents
            )
        )