from pathlib import Path


class InputDetector:


    def detect(self, data):

        if isinstance(data, str):

            return "text"


        if isinstance(data, bytes):

            return "binary"


        if isinstance(data, Path):

            extension = data.suffix.lower()


            if extension in [
                ".png",
                ".jpg",
                ".jpeg",
                ".webp"
            ]:
                return "image"


            if extension == ".pdf":
                return "pdf"


            if extension in [
                ".doc",
                ".docx"
            ]:
                return "document"


        return "unknown"