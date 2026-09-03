"""
OM Multimodal Intelligence Agent
"""


from .fusion import FeatureFusion

from .context import MultimodalContext

from .understanding import MultimodalUnderstanding

from .memory import MultimodalMemory

from .router import ModalityRouter





class MultimodalAgent:



    def __init__(self):


        self.fusion = FeatureFusion()

        self.context = MultimodalContext()

        self.understanding = MultimodalUnderstanding()

        self.memory = MultimodalMemory()

        self.router = ModalityRouter()



    def process(

        self,

        input_data

    ):


        modalities=self.router.detect(

            input_data

        )


        features=self.fusion.combine(

            input_data

        )


        context=self.context.build(

            features

        )


        result=self.understanding.understand(

            context

        )


        result["modalities"]=modalities



        self.memory.store(

            result

        )


        return result