"""
OM Agent Knowledge Tool Orchestrator

Central execution controller.
"""


from .execution_plan import ExecutionPlan

from .context_builder import ContextBuilder

from .result import OrchestrationResult





class OMOrchestrator:



    def __init__(self):


        self.context_builder = ContextBuilder()



    def create_plan(

        self,

        agent_result:dict,

        question:str

    ):


        agent_name = agent_result.get(

            "name",

            "general"

        )



        tools=[]



        if agent_name == "coding":

            tools=[

                "code_executor",

                "documentation_search"

            ]



        elif agent_name == "research":

            tools=[

                "knowledge_search"

            ]



        return ExecutionPlan(

            agent=agent_name,

            tools=tools,

            knowledge_required=True,

            memory_required=True,

            steps=[

                "retrieve knowledge",

                "load memory",

                "execute tools",

                "generate solution",

                "evaluate result"

            ]

        )





    def orchestrate(

        self,

        question:str,

        agent_result:dict,

        *,


        memory=None,

        knowledge=None,

        tools=None

    ):



        plan=self.create_plan(

            agent_result,

            question

        )



        context=self.context_builder.build(

            question=question,

            agent=agent_result,

            memory=memory,

            knowledge=knowledge,

            tools=tools

        )



        return {


            "plan":

                plan.to_dict(),


            "context":

                context

        }