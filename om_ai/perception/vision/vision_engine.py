from .image_analyzer import ImageAnalyzer


class VisionEngine:


    def __init__(self):

        self.analyzer = ImageAnalyzer()



    def analyze(
        self,
        image_path: str
    ):


        result = self.analyzer.process(
            image_path
        )


        return result