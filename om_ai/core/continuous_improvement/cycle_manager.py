from __future__ import annotations



class ImprovementCycleManager:


    def __init__(self):

        self.cycles=[]



    def start(
        self,
        plan
    ):


        cycle={

            "plan":plan,

            "status":"started"

        }


        self.cycles.append(
            cycle
        )


        return cycle



    def complete(
        self,
        cycle
    ):

        cycle["status"]="completed"