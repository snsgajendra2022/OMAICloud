class PDFReader:


    def read(self, file_path):

        return {

            "file":
                file_path,

            "status":
                "pdf_loaded",

            "pages":
                0,

            "text":
                ""

        }