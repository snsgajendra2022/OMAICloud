from pathlib import Path


class DocumentDetector:


    def detect(self, file_path):

        extension = Path(file_path).suffix.lower()


        mapping = {

            ".pdf": "pdf",

            ".docx": "word",

            ".doc": "word",

            ".xlsx": "excel",

            ".xls": "excel"

        }


        return mapping.get(
            extension,
            "unknown"
        )