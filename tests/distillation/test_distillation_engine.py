from om_ai.core.distillation import (
    DistillationEngine,
)



class FakeTeacher:


    class Result:

        def __init__(
            self,
            teacher,
            response
        ):

            self.teacher = teacher
            self.response = response



    def ask_teachers(
        self,
        question
    ):

        return [

            self.Result(
                "qwen",
                "React is a JavaScript UI library using reusable components."
            ),

            self.Result(
                "deepseek",
                "React helps developers build component based interfaces."
            )

        ]



def test_pipeline():


    engine = DistillationEngine(

        teacher_manager=
            FakeTeacher()

    )


    result = engine.distill(

        "Explain React",

        "software"

    )


    assert result["approved"]

    assert result["knowledge"]
