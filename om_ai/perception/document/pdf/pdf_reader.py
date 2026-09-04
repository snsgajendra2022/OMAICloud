import pymupdf


class PDFReader:


    def extract_text(self, file_path):

        doc = pymupdf.open(file_path)

        pages=[]


        for page in doc:

            pages.append(
                page.get_text()
            )


        return "\n".join(pages)