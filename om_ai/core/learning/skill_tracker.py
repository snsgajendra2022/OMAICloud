class SkillTracker:


    def __init__(self):

        self.skills={}



    def update(
        self,
        skill,
        score
    ):

        self.skills[skill]=score



    def get(
        self,
        skill
    ):

        return self.skills.get(
            skill,
            0
        )