from .vision_engine import VisionEngine


class VisionManager:


    def __init__(self):

        self.engine = VisionEngine()



    def process_image(
        self,
        image_path
    ):


        return self.engine.analyze(
            image_path
        )