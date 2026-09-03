"""
OM Personal Intelligence Engine
"""


from .profile import UserProfile

from .graph import PersonalGraph

from .extractor import UserExtractor

from .preference import PreferenceMemory





class UserIntelligenceEngine:



    def __init__(self):


        self.profile = UserProfile(

            user_id="default"

        )


        self.graph = PersonalGraph()

        self.extractor = UserExtractor()

        self.preferences = PreferenceMemory()




    def learn(

        self,

        interaction:str

    ):


        data=self.extractor.extract(

            interaction

        )


        for tech in data["technologies"]:

            self.profile.add_unique(

                self.profile.technologies,

                tech

            )


            self.graph.add({

                "entity":

                    tech,

                "type":

                    "technology",

                "relation":

                    "uses"

            })



        for project in data["projects"]:

            self.profile.add_unique(

                self.profile.projects,

                project

            )



        return self.profile.to_dict()




    def profile_data(self):


        return self.profile.to_dict()