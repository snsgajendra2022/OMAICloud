from om_ai.core.distillation import (
    OllamaClient,
    TeacherRegistry
)


def initialize_teacher_registry():

    client = OllamaClient()


    registry = TeacherRegistry(
        client,
        []
    )


    if client.health_check()["status"] == "healthy":

        models = client.list_models()

        print(
            "Available Ollama Teachers:"
        )

        for model in models:

            print(
                "✓",
                model
            )


        return registry


    print(
        "Ollama unavailable - skipping teachers"
    )


    return None