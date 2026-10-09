from om_ai.core.response.answer_generator import AnswerGenerator


generator = AnswerGenerator()


reasoning = {

    "understanding": {

        "technology":
        "React Native"

    },

    "plan": [

        "Create Login Screen",

        "Create Dashboard Screen",

        "Setup Navigation",

        "Add Authentication",

        "Test Application"

    ]

}


answer = generator.generate(
    "create react native login dashboard app",
    reasoning
)


print(answer)