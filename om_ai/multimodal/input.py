"""
OM Multimodal Input Model
"""


from dataclasses import dataclass, field





@dataclass
class MultimodalInput:


    text:str = ""


    audio:any = None


    image:any = None


    document:any = None


    metadata:dict = field(

        default_factory=dict

    )



    def to_dict(self):

        return {


            "text":

                self.text,


            "audio":

                self.audio,


            "image":

                self.image,


            "document":

                self.document,


            "metadata":

                self.metadata

        }