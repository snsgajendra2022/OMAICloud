from .text_extractor import TextExtractor


class OCREngine:


    def __init__(self):

        self.extractor = TextExtractor()



    def process(self, image_path):

        text = self.extractor.extract(
            image_path
        )


        return {

            "text": text,

            "confidence": 0.0,

            "source": image_path

        }