"""
OM User Preference Memory
"""





class PreferenceMemory:



    def __init__(self):

        self.preferences={}




    def remember(

        self,

        key,

        value

    ):


        self.preferences[key]=value




    def get(

        self,

        key,

        default=None

    ):


        return self.preferences.get(

            key,

            default

        )