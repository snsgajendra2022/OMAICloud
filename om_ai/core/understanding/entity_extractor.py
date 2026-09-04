class EntityExtractor:


    def extract(self, text):

        entities={}


        lower=text.lower()


        if "react" in lower:

            entities["technology"]="react"


        if "python" in lower:

            entities["technology"]="python"


        if "date" in lower:

            entities["topic"]="date"


        if "music" in lower:

            entities["topic"]="music"


        return entities