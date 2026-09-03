"""
OM Vision Manager
"""


from .vision_agent import VisionAgent




class VisionManager:



    def __init__(self):


        self.agent=VisionAgent()



    def process(

        self,

        image

    ):


        return self.agent.understand(

            image

        )