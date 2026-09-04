class LearningState:


    def __init__(self):

        self.total_experiences = 0

        self.improvements = 0



    def add_experience(self):

        self.total_experiences += 1



    def add_improvement(self):

        self.improvements += 1