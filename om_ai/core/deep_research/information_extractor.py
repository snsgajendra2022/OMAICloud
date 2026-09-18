class InformationExtractor:



    def extract(
        self,
        document
    ):


        content=document["content"]


        return {


            "facts":

                content.split(".")[:10],


            "source":

                document["title"]

        }