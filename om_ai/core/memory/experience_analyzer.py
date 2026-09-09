class ExperienceAnalyzer:



    def analyze(
        self,
        message
    ):


        experiences=[]


        text = message.lower()


        patterns = {


            "coding":
            [
                "created",
                "built",
                "developed",
                "implemented"
            ],


            "learning":
            [
                "learned",
                "studied",
                "understood"
            ]

        }



        for category, words in patterns.items():


            for word in words:

                if word in text:


                    experiences.append({

                        "type":
                        category,


                        "content":
                        message

                    })


        return experiences