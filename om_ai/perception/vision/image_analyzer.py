from .object_detector import ObjectDetector


class ImageAnalyzer:


    def __init__(self):

        self.object_detector = ObjectDetector()



    def process(
        self,
        image_path
    ):


        objects = self.object_detector.detect(
            image_path
        )


        return {

            "image":
                image_path,


            "objects":
                objects,


            "description":
                "Image analyzed successfully",


            "confidence":
                0.0

        }