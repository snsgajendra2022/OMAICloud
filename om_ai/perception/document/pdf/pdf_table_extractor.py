import pdfplumber


class PDFTableExtractor:


    def extract(self,file_path):

        tables=[]


        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:

                page_tables = page.extract_tables()

                if page_tables:

                    tables.extend(page_tables)


        return tables