"""
OM Multimodal Feature Fusion Engine
"""


class FeatureFusion:



    def combine(

        self,

        inputs:dict

    ):


        context=[]



        if inputs.get("text"):

            context.append(

                {

                    "type":

                    "text",

                    "value":

                    inputs["text"]

                }

            )



        if inputs.get("audio"):

            context.append(

                {

                    "type":

                    "audio",

                    "value":

                    inputs["audio"]

                }

            )



        if inputs.get("image"):

            context.append(

                {

                    "type":

                    "image",

                    "value":

                    inputs["image"]

                }

            )



        if inputs.get("document"):

            context.append(

                {

                    "type":

                    "document",

                    "value":

                    inputs["document"]

                }

            )



        return context