class DocumentReader:



    def read(
        self,
        document
    ):


        return {


            "title":
                document.title,


            "content":
                document.content,


            "length":
                len(
                    document.content
                )

        }