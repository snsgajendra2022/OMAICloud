"""
OM Intelligent File Selector
"""


class FileSelector:



    def select(

        self,

        files,

        requirement

    ):


        selected=[]


        words=requirement.lower().split()



        for file in files:


            path=file.get(

                "file",

                ""

            ).lower()



            for word in words:


                if word in path:

                    selected.append(file)

                    break



        return selected[:10]