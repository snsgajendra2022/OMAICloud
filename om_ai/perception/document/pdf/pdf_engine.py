from .pdf_reader import PDFReader
from .pdf_metadata import PDFMetadata
from .pdf_table_extractor import PDFTableExtractor
from .pdf_image_extractor import PDFImageExtractor
from .pdf_structure import PDFStructureAnalyzer
from .semantic.semantic_engine import SemanticEngine

class PDFEngine:


    def __init__(self):

        self.reader = PDFReader()

        self.metadata = PDFMetadata()

        self.tables = PDFTableExtractor()

        self.images = PDFImageExtractor()

        self.structure = PDFStructureAnalyzer()
        self.semantic = SemanticEngine()



    def analyze(self,file_path):


        text = self.reader.extract_text(
            file_path
        )
        semantic = self.semantic.understand(
            text
        )

        return {

            "metadata":
                self.metadata.extract(
                    file_path
                ),


            "text":
                text,


            "tables":
                self.tables.extract(
                    file_path
                ),


            "images":
                self.images.extract(
                    file_path
                ),


            "structure":
                self.structure.analyze(
                    text
                ),
            "semantic": semantic

        }