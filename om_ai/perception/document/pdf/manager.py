from .pdf_engine import PDFEngine



class PDFManager:


    def __init__(self):

        self.engine = PDFEngine()



    def process(self,file_path):


        result = self.engine.analyze(
            file_path
        )


        return {

            "type":
                "pdf_document",

            "data":
                result

        }