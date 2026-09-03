"""
OM User Intelligence Profile
"""


from dataclasses import dataclass, field





@dataclass
class UserProfile:


    user_id: str


    name: str = ""


    skills: list[str] = field(
        default_factory=list
    )


    technologies: list[str] = field(
        default_factory=list
    )


    projects: list[str] = field(
        default_factory=list
    )


    preferences: dict = field(
        default_factory=dict
    )



    def add_unique(

        self,

        collection,

        value

    ):


        if value and value not in collection:

            collection.append(value)



    def to_dict(self):

        return {

            "user_id":

                self.user_id,

            "name":

                self.name,

            "skills":

                self.skills,

            "technologies":

                self.technologies,

            "projects":

                self.projects,

            "preferences":

                self.preferences

        }