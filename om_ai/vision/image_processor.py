"""
OM Image Processing Layer

Handles:

- Image loading
- Metadata extraction
- Basic preprocessing
"""


from pathlib import Path



class ImageProcessor:


    def load(

        self,

        image_path:str

    ):


        path = Path(image_path)


        return {


            "path":

                str(path),


            "exists":

                path.exists(),


            "format":

                path.suffix.lower()

        }