from __future__ import annotations



class TeacherRegistry:
    """
    Tracks available Ollama teachers.
    """


    def __init__(
        self,
        ollama_client,
        configured_models=None
    ):


        self.client = ollama_client


        self.configured_models = (
            configured_models
            or []
        )



    def installed_models(self):

        return (
            self.client
            .list_models()
        )



    def available_teachers(self):

        installed = (
            self.installed_models()
        )


        return [

            model

            for model
            in self.configured_models

            if model in installed

        ]

    def get_ready_models(self):
        """Compatibility helper for TeacherManager.ask_teachers()."""
        from .models import TeacherModel

        return [
            TeacherModel(name=name, available=True)
            for name in self.available_teachers()
        ]

    def status(self):

        installed = (
            self.installed_models()
        )


        return [

            {

                "model":
                    model,

                "available":
                    model in installed

            }

            for model
            in self.configured_models

        ]