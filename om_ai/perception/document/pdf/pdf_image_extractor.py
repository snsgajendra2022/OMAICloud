import pymupdf

class PDFImageExtractor:


    def extract(self,file_path):

        doc = pymupdf.open(file_path)

        images=[]


        for page_index,page in enumerate(doc):

            for img in page.get_images():

                images.append({

                    "page":
                        page_index,

                    "image":
                        img[0]

                })


        return images