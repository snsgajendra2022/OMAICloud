"""
OM Vision Intelligence Agent
"""


from .image_processor import ImageProcessor

from .ocr import OCRProcessor

from .object_detection import ObjectDetector

from .analyzer import VisionAnalyzer

from .memory import VisionMemory





class VisionAgent:



    def __init__(self):


        self.processor = ImageProcessor()

        self.ocr = OCRProcessor()

        self.detector = ObjectDetector()

        self.analyzer = VisionAnalyzer()

        self.memory = VisionMemory()



    def understand(

        self,

        image_path

    ):


        image=self.processor.load(

            image_path

        )


        text=self.ocr.extract_text(

            image

        )


        objects=self.detector.detect(

            image

        )


        combined={


            **image,


            **text,


            **objects

        }


        result=self.analyzer.analyze(

            combined

        )


        self.memory.store(

            result

        )


        return result