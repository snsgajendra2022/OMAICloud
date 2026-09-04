import pymupdf


class PDFMetadata:


    def extract(self, file_path):

        doc = pymupdf.open(file_path)

        metadata = doc.metadata


        return {

            "title":
                metadata.get("title",""),

            "author":
                metadata.get("author",""),

            "pages":
                len(doc)

        }