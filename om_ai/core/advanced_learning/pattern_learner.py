class PatternLearner:


    def learn(
        self,
        records
    ):


        patterns={}


        for record in records:

            text = (
                record.input_data.lower()
            )


            words = text.split()


            for word in words:

                patterns[word] = (
                    patterns.get(word,0)+1
                )


        important=[]


        for key,value in patterns.items():

            if value >= 2:

                important.append(key)


        return important