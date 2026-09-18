from .model_router import ModelRouter
from .intelligence_selector import IntelligenceSelector
from .response_fusion import ResponseFusion
from .quality_controller import QualityController



class IntelligenceEngine:



    def __init__(
        self,
        registry,
        capability
    ):


        self.router = ModelRouter(
            registry,
            capability
        )


        self.selector = IntelligenceSelector()


        self.fusion = ResponseFusion()


        self.quality = QualityController()



    def execute(
        self,
        task:str,
        executor
    ):


        models = self.router.route(
            task
        )


        selected = self.selector.select(
            models
        )


        responses=[]


        for model in selected:


            result = executor(
                model,
                task
            )


            responses.append(
                result
            )



        final = self.fusion.combine(
            responses
        )


        answer_text = ""
        if isinstance(final, dict):
            answer_text = str(final.get("answer") or "")
        elif final is not None:
            answer_text = str(final)

        quality = self.quality.evaluate(
            answer_text
        )



        return {


            "answer":

            answer_text,


            "fusion":

            final if isinstance(final, dict) else {"answer": answer_text},


            "quality":

            quality,


            "models":

            [
                m.name
                for m in selected
            ]

        }