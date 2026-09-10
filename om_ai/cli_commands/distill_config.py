from dataclasses import dataclass
import os


@dataclass
class DistillationCLIConfig:


    enabled: bool = True


    ollama_url: str = ( os.getenv("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434") )


    output: str = "data/distillation"



    @classmethod
    def load(cls):

        return cls(

            enabled=os.getenv(
                "OM_DISTILLATION_ENABLED",
                "true"
            ).lower()=="true",


            ollama_url=os.getenv(

                "OM_OLLAMA_BASE_URL",

                "http://127.0.0.1:11434"

            )

        )