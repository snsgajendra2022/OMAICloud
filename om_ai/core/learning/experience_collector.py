from .experience import Experience

class ExperienceCollector:


    def collect(
        self,
        message,
        response,
        metadata=None
    ):


        return Experience(

            input_message=message,

            response=response,

            metadata=metadata or {}

        )