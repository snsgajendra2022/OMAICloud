"""
OM Multimodal Context Builder
"""



class MultimodalContext:



    def build(

        self,

        features,

        memory=None

    ):


        return {


            "features":

                features,


            "memory":

                memory or [],


            "count":

                len(features)

        }