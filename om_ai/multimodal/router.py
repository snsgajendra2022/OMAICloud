"""
OM Modality Router
"""



class ModalityRouter:



    def detect(

        self,

        inputs

    ):


        active=[]



        for key,value in inputs.items():


            if value:

                active.append(

                    key

                )


        return active